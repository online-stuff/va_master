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
    sys.stdout.write('%s\n' % msg)

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


def handle_init(args):
    """Handles cli `start` command. Should write proper conf and start daemon."""
    # If optional arguments weren't specified, interactively ask.
    attrs = [
        ('ip', 'Enter the IPv4 addr. of this machine'),
        ('admin_user', 'Enter username for the first admin'),
        ('admin_pass', 'Enter password for the first admin'), 
        ('salt_master_fqdn', 'Enter the fqdn for the salt master'),
    ]
    values = {}
    print dir(args)
    for attr in attrs:
        name = attr[0]
        cmdhelp = attr[1]
        values[name] = getattr(args, name)
        if values[name] is None: # The CLI `args` doesn't have it, ask.
            values[name] = raw_input('%s: ' % cmdhelp)
    result = True # If `result` is True, all actions completed successfully
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
        from . import datastore
        store = datastore.ConsulStore()
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
            # We have a connection, create an admin account
            create_admin = functools.partial(login.create_admin,
                store, values['admin_user'], values['admin_pass'])

            #Store some stuff in datastore
            store_ip = functools.partial(store.insert, 'master_ip', values['ip'])
            #TODO get flavours from github or something
            libvirt_flavours = {'va-small' : {'vol_capacity' : 5, 'memory' : 2**20, 'max_memory' : 2**20, 'num_cpus' : 1}}
            salt_fqdn = functools.partial(store.insert, 'salt_master_fqdn', values['salt_master_fqdn'])
            store_flavours = functools.partial(store.insert, 'libvirt_flavours', libvirt_flavours)

            run_sync(create_admin)
            run_sync(store_ip)
            run_sync(store_flavours)
            run_sync(salt_fqdn)


            #Generate an ssh-key
            os.mkdir('/root/va_master_key')
            ssh_cmd = ['ssh-keygen', '-t', 'rsa', '-f', '/root/va_master_key/va_master_key_name', '-N', '""']

            #TODO a keypair

            subprocess.call(ssh_cmd)

            cli_success('Created first account. Setup is finished.')

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
    init_sub.add_argument('--ip', help='The IP of this machine, which is ' + \
        'going to be advertised to apps')
    init_sub.add_argument('--admin-user', help='Username of the first admin')
    init_sub.add_argument('--admin-pass', help='Password of the first admin')
    init_sub.add_argument('--salt-master-fqdn', help='Enter the fqdn for the salt master')

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
