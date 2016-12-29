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

consul_conf_path = '/etc/consul.json'

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
        'libvirt_flavours' : 
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


def handle_init(args):
    """Handles cli `start` command. Should write proper conf and start daemon."""
    # If optional arguments weren't specified, interactively ask.
    attrs = [
        ('ip', 'Enter the IPv4 addr. of this machine'),
        ('admin_user', 'Enter username for the first admin'),
        ('admin_pass', 'Enter password for the first admin'), 
        ('salt_master_fqdn', 'Enter the fqdn for the salt master'),
        ('salt_key_path', 'Enter the path to the salt key. '), 
        ('salt_key_name', 'Enter the name of the salt key. '), 
        ('host_vpn_endpoint', 'Enter the VPN endpoint. Will default to vpn.<salt_master_fqdn>' ),
        ('company_name', 'The name of Your company. It will be used in the VPN certifiates. ')
    ]
    values = {}
    
    if args.skip_args: 
        cli_info('Setting up the va_master module without prompting for arguments. If this is the first time you are setting up the environment, you might want to make sure you enter all arguments or run init again without skip_args. ')

    for attr in attrs:
        name = attr[0]
        cmdhelp = attr[1]
        values[name] = getattr(args, name)
        if (values[name] is None) and not args.skip_args: # The CLI `args` doesn't have it, ask.
            values[name] = raw_input('%s: ' % cmdhelp)

    if not values['host_vpn_endpoint'] and values['salt_master_fqdn']: 
        values['host_vpn_endpoint'] = 'vpn.' + values['salt_master_fqdn']

    values = {k: v for k, v in values.items() if v}
    result = True # If `result` is True, all actions completed successfully
    if values.get('ip'): 
        try:
            cli_environment.write_supervisor_conf()
            cli_success('Configured Supervisor.')
        except:
            cli_error('Failed configuring Supervisor: ')
            traceback.print_exc()
            result = False # We failed with step #1
        try:
            cli_environment.write_consul_conf(values['ip'])
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


        from .api import login
        cli_config = config.Config(init_vals = values)

#        from . import datastore
        store = cli_config.datastore
        run_sync = tornado.ioloop.IOLoop.instance().run_sync
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
        else:

            try:
                cli_info('Trying to start VPN. ')
                if values.get('host_vpn_endpoint'): 
                    cli_environment.write_vpn_pillar(values['host_vpn_endpoint']) 
                cli_success('VPN is running. ')
            except: 
                cli_error('Failed to start VPN. Error was : ')
                import traceback
                traceback.print_exc()

 
            # We have a connection, create an admin account
            if values.get('admin_user') and values.get('admin_pass'): 
                create_admin = functools.partial(login.create_admin,
                    store, values['admin_user'], values['admin_pass'])
                create_admin_run = run_sync(create_admin)

            states_data = run_sync(functools.partial(cli_config.deploy_handler.get_states_data))
            values.update({'states' : states_data})


            try:
                store_config = run_sync(functools.partial(store.get, 'init_vals')) or {}
            except: 
                store_config = {}

            store_config.update(generate_store_config(values))
            
#            store_config = run_sync(functools.partial(store.insert, 'init_vals', store_config))
            run_sync(functools.partial(store.insert, 'init_vals', store_config))

            try:
                panels = run_sync(functools.partial(store.get, 'panels')) or {'admin' : [], 'user' : []}
            except: 
                run_sync(functools.partial(store.insert, 'panels', {'admin' : {}, 'user' : {}}))


            #Generate an ssh-key
            if values.get('salt_key_path') and values.get('salt_key_name'): 
                values['salt_key_path'] = values['salt_key_path'] + '/' * (values['salt_key_path'][-1] != '/')
                try: 
                    try: 
                        os.mkdir(values['salt_key_path'])
#                        os.mkdir('/root/va_master_key')
                    except: 
                        pass
                    key_full_path = values['salt_key_path'] + values['salt_key_name']

                    ssh_cmd = ['ssh-keygen', '-t', 'rsa', '-f', key_full_path, '-N', '']

#                    ssh_cmd = ['ssh-keygen', '-t', 'rsa', '-f', '/root/va_master_key/va_master_key_name', '-N', '']

                    subprocess.call(ssh_cmd)
                    subprocess.call(['mv', key_full_path, key_full_path + '.pem'])
                except: 
                    import traceback
                    print ('Could not generate a key. Probably already exists. ')
                    traceback.print_exc()

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

def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')
    subparsers = parser.add_subparsers(help='action')

    init_sub = subparsers.add_parser('init', help='Initializes and starts server')
    
    expected_args = [
        ('ip', 'Enter the IPv4 addr. of this machine'),
        ('admin-user', 'Enter username for the first admin'),
        ('admin-pass', 'Enter password for the first admin'), 
        ('salt-master_fqdn', 'Enter the fqdn for the salt master'),
        ('salt-key-path', 'Enter the path to the salt key. '), 
        ('salt-key-name', 'Enter the name of the salt key. '), 
        ('host-vpn-endpoint', 'Enter the VPN endpoint. Will default to vpn.<salt_master_fqdn>' ),
        ('company-name', 'The name of Your company. It will be used in the VPN certifiates. ')
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

    args = parser.parse_args()
    # Define handlers for each subparser
    handlers = {
        'init': handle_init,
        'jsbuild': handle_jsbuild,
        'stop': lambda x: None
    }
    # Call the proper handler based on the subparser argument
    handlers[args.sub](args)

if __name__ == '__main__': 
    entry()
