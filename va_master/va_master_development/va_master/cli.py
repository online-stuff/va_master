import config, cli_environment
from api import login
from datetime import datetime
import tornado.ioloop
import yaml, json, glob
import os
import sys
import time
import argparse
import subprocess
import distutils
import traceback
import functools
import imp
from .api import login

consul_conf_path = '/etc/consul.json'
run_sync = tornado.ioloop.IOLoop.instance().run_sync


def is_cli():
    # TODO: Find a way to separate a CLI entrypoint execution versus
    # a standard module import
    return True

def cli_info(msg):
    """Outputs a CLI information message to the console."""
    if not is_cli(): return

    sys.stdout.write('%(yellow)s[info]%(nocolor)s %(msg)s\n' % {
        'yellow': '\033[93m',
        'nocolor': '\033[0m',
        'msg': msg
    })

def cli_success(msg):
    """Outputs a CLI success message to the console."""
    if not is_cli(): return
    sys.stdout.write('%(green)s[success]%(nocolor)s %(msg)s\n' % {
        'green': '\033[92m',
        'nocolor': '\033[0m',
        'msg': msg
    })

def cli_error(msg):
    """Outputs a CLI error message to the console."""
    if not is_cli(): return
    sys.stderr.write('%(red)s[error]%(nocolor)s %(msg)s\n' % {
        'red': '\033[91m',
        'nocolor': '\033[0m',
        'msg': msg
    })


def generate_store_config(values):
    store_config = {
        'va_flavours' : 
        {
            'va-small' : 
            {
                'vol_capacity' : 5, 
                'memory' : 2**20, 
                'max_memory' : 2**20, 
                'num_cpus' : 1
            }, 
            'debian' : 
            {
                'vol_capacity' : 5, 
                'memory' : 2**20, 
                'max_memory' : 2**20, 
                'num_cpus' : 1
            }
        }
    }
    store_config.update(values)

    return store_config

def get_values_from_args(args):
    # If optional arguments weren't specified, interactively ask.
    attrs = [
        ('company-name', 'The name of Your company. It will be used in the VPN certifiates [VapourApps cloud] '),
        ('domain_name', 'Enter the default domain name for this installation [va.mk]'),
        ('fqdn', 'Enter an IP address of FQDN [master.va.mk]'),
        ('admin-user', 'Enter username for the first admin [admin]'),
        ('admin-pass', 'Enter password for the first admin [admin]'),
        ('vpn-port', 'Enter the OpenVPN port accesible from Internet to this host [8443]'),
    ]
    values = {}
   
    if args.get('skip_args'): 
        cli_info('Setting up the va_master module without prompting for arguments. If this is the first time you are setting up the environment, you might want to make sure you enter all arguments or run init again without skip_args. ')

    for attr in attrs:
        name = attr[0].replace('-', '_')
        cmdhelp = attr[1]
        values[name] = args.get(name)
        if (values[name] is None) and not args.get('skip_args'): # The CLI `args` doesn't have it, ask.
            values[name] = raw_input('%s: ' % cmdhelp)

    values = {k: v for k, v in values.items() if v}
    return values

def handle_configurations(fqdn = None):
    result = True
    if fqdn:
        try:
            cli_environment.write_supervisor_conf()
            cli_success('Configured Supervisor.')
        except:
            cli_error('Failed configuring Supervisor: ')
            traceback.print_exc()
            result = False # We failed with step #1
        try:
            cli_environment.write_consul_conf(fqdn)
            cli_success('Configured Consul.')
        except:
            import traceback
            cli_error('Failed configuring Consul: ')
            traceback.print_exc()
            result = False # We failed with step #2

        if not result:
            cli_error('Initialization failed because of one or more errors.')
            sys.exit(1)
    else:
        try:
            cli_environment.reload_daemon()
            cli_success('Started daemon.')
        except:
            cli_error('Failed reloading the daemon, check supervisor logs.' + \
            '\nYou may try `service supervisor restart` or ' + \
            '/var/log/supervisor/supervisord.log')
            traceback.print_exc()
            sys.exit(1)



def check_datastore_connection(values, store):
    attempts, failed = 1, True
    cli_info('Waiting for the key value store to come alive...')
    while attempts <= cli_environment.DATASTORE_ATTEMPTS:
        is_running = run_sync(store.check_connection)
        cli_info('  -> attempt #%i...' % attempts)
        if is_running:
            failed = False
            break
        else:
            time.sleep(cli_environment.DATASTORE_RETRY_TIME)
            attempts+= 1
    if failed:
        cli_error('Store connection timeout after %i attempts.' \
            % attempts)
        sys.exit(1)

    try:
        cli_info('Trying to start VPN. ')
        cli_environment.write_vpn_pillar(values['domain_name']) 
        cli_success('VPN is running. ')
    except: 
        cli_error('Failed to start VPN. Error was : ')
        import traceback
        traceback.print_exc()

    return not failed

def create_admin_user(admin_user, admin_pass, store):
    if admin_user and admin_pass: 
        create_user = functools.partial(login.create_user,
            store, admin_user, admin_pass, 'admin')
        create_user_run = run_sync(create_user)
    else: 
        cli_info('No username and password; will not create user')

def handle_store_init(cli_config, values, store):
    states_data = run_sync(functools.partial(cli_config.deploy_handler.get_states_data))
    values.update({'states' : states_data})

    try:
        store_config = run_sync(functools.partial(store.get, 'init_vals')) or {}
    except: 
        store_config = {}

    store_config.update(generate_store_config(values))
    store_config = {x : store_config[x] for x in store_config if x not in ['admin_pass']}
#            store_config = run_sync(functools.partial(store.insert, 'init_vals', store_config))
    run_sync(functools.partial(store.insert, 'init_vals', store_config))

    #Add va_standalone_servers
    run_sync(functools.partial(store.insert, 'providers', [{"username": "admin", "sizes": [], "servers": [], "images": [], "driver_name": "generic_driver", "location": "va_master", "defaults": {}, "sec_groups": [], "provider_name": "va_standalone_servers", "password": "admin", "ip_address": "127.0.0.1", "networks": []}]))
    run_sync(functools.partial(store.insert, 'va_standalone_servers', {"servers" : []}))

    return store_config

def add_initial_panels(store):
    try:
        panels = run_sync(functools.partial(store.get, 'panels')) or {'admin' : [], 'user' : []}
    except: 
        run_sync(functools.partial(store.insert, 'panels', {'admin' : [], 'user' :[]}))

def create_ssh_keys(store_config):
    try: 
#            os.mkdir(cli_config.ssh_key_path)
        key_full_path = cli_config.ssh_key_path + cli_config.ssh_key_name
        ssh_cmd = ['ssh-keygen', '-t', 'rsa', '-f', key_full_path, '-N', '']
        
        subprocess.call(ssh_cmd)
        subprocess.call(['mv', key_full_path, key_full_path + '.pem'])
    except: 
        import traceback
        print ('Could not generate a key. Probably already exists. ')
        traceback.print_exc()

def handle_init(args):
    """Handles cli `start` command. Should write proper conf and start daemon."""

    values = get_values_from_args(args)

    result = True # If `result` is True, all actions completed successfully

    handle_configurations(values.get('fqdn'))

    cli_config = config.Config(init_vals = values)

    store = cli_config.datastore

    check_datastore_connection(values, store)
    create_admin_user(values.get('admin_user'), values.get('admin_pass'), store)
    store_config = handle_store_init(cli_config, values, store)
    add_initial_panels(store)



    #Generate an ssh-key
    create_ssh_keys(store_config)

    cli_success('Created first account. Setup is finished.')
    cli_config.init_handler(init_vals = values)


def handle_jsbuild(args):
    try:
        build_path = os.path.join(os.path.dirname(__file__), 'dashboard',
            'build.js')
        build_path = os.path.abspath(build_path)
        subprocess.check_call(['node', build_path])
    except (OSError, subprocess.CalledProcessError):
        cli_error('An error occured during compile invocation. Make sure' + \
        ' NodeJS interpreter is in PATH, with name `node`.')
        traceback.print_exc()
    else:
        cli_success(('Compiled JS using the command `node %s`, into `' + \
            'dashboard/static/*`') % build_path)


def handle_add_module(args):
    file_path = args['module_path']
    file_name = file_path.split('/')[-1]
    file_contents = ''
    with open(file_path, 'r') as f: 
        file_contents = f.read()
    cli_info('Read file ' + file_path)

    try: 
        new_module = imp.load_source(file_name, file_path)
        cli_info('Imported module. Checking for get_paths()')
        
        paths = getattr(new_module, 'get_paths')()
        paths_list = {}

        for key in ['get', 'post', 'delete', 'put']: 
            paths_list.update(paths.get(key, {}))

        for path in paths_list: 
            if not callable(paths_list[path]): 
                raise Exception('Attribute ' +  str(paths_list[path]) + ' is not callable. ')
    except Exception as e: 
        cli_error('Error adding module: ' + e.message)
        return
        #TODO more checks. 
    cli_success('Module looks fine. Adding to api. ')

    va_path = '/'.join((os.path.realpath(__file__).split('/')[:-1]))
    api_path = os.path.join(va_path, 'api/')
    with open(api_path + file_name, 'w') as f: 
        f.write(file_contents)
    cli_success('Module copied to : ' + api_path + file_name)
        
    
def handle_new_user(args):
    from .api import login
    cli_config = config.Config()

    store = cli_config.datastore

    run_sync = tornado.ioloop.IOLoop.instance().run_sync
    user_type = 'user' if args.get('ordinary_user') else 'admin'
    create_user = functools.partial(login.create_user, store, args['username'], args['password'], user_type)
    create_user_run = run_sync(create_user)
   
def handle_test_api(args):
    from .api import api_test
    test_cl = api_test.TestAPIMethods(args['token'], args['base_url'])
    if args['generate_endpoints']: 
        test_cl.generate_api_endpoints()
    else: 
        path = {}
        with open('api_endpoints.json') as f: 
            paths = json.loads(f.read())
        print paths
        test_cl.set_paths(paths)
        test_cl.test_api_endpoints()



def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')
    subparsers = parser.add_subparsers(help='action')

    init_sub = subparsers.add_parser('init', help='Initializes and starts server')
    expected_args = [
        ('company-name', 'The name of Your company. It will be used in the VPN certifiates [VapourApps cloud] '),
        ('domain_name', 'Enter the default domain name for this installation [va.mk]'),
        ('fqdn', 'Enter an IP address of FQDN [master.va.mk]'),
        ('admin-user', 'Enter username for the first admin [admin]'),
        ('admin-pass', 'Enter password for the first admin [admin]'),
        ('vpn-port', 'Enter the OpenVPN port accesible from Internet to this host [8443]'),
    ]
    for arg in expected_args: 
        init_sub.add_argument('--' + arg[0], help = arg[1])
    init_sub.add_argument('--skip-args', help = 'If set, the cli will not prompt you for values for arguments which were not supplied. ', action = 'store_true')

    # args.sub will equal 'start' if this subparser is used
    init_sub.set_defaults(sub='init')

    jsbuild_sub = subparsers.add_parser('jsbuild', help='Compiles and' + \
    ' minifies JavaScript')
    jsbuild_sub.set_defaults(sub='jsbuild')

    stop_sub = subparsers.add_parser('stop', help='Stops the server')
    stop_sub.set_defaults(sub='stop')

    add_module = subparsers.add_parser('add_module', help='Adds an api module. Check the documentation on how to write api modules. ')
    add_module.add_argument('--module-path', help = 'Path to the python module. ')

    add_module.set_defaults(sub='add_module')

    new_user = subparsers.add_parser('new_user', help='Creates a new user.  ')
    new_user.add_argument('--username', help = 'The username for the user. ')
    new_user.add_argument('--password', help = 'The password. Will be hashed in the datastore.  ')
    new_user.add_argument('--ordinary-user', help = 'If set, will create a normal user instead of an admin. ', action = 'store_true', default = False)

    new_user.set_defaults(sub='new_user')

    test_api = subparsers.add_parser('test-api', help='Runs through (some of) the API endpoints and tests their results. ')
    test_api.add_argument('--token', help = 'Enter the token which the test suite will use. ')
    test_api.add_argument('--generate-endpoints', help = 'If set to True, it will generate an api_endpoints.json file which you can edit to set up default arguments for all the functions. You may delete functions that you do not want in the test from this file. ', dest = 'generate_endpoints', action = 'store_true')
    test_api.add_argument('--base-url', help = 'Enter the base url. Default : 127.0.0.1', default = 'https://127.0.0.1:443/api/')
    test_api.set_defaults(sub='test_api')

    args = parser.parse_args()
    # Define handlers for each subparser
    handlers = {
        'init': handle_init,
        'jsbuild': handle_jsbuild,
        'add_module' : handle_add_module,
        'new_user' : handle_new_user,
        'test_api' : handle_test_api,
        'stop': lambda x: None
    }
    # Call the proper handler based on the subparser argument
    handlers[args.sub](vars(args))

if __name__ == '__main__': 
    entry()