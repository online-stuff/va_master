from . import config, environment
from .api import login
from datetime import datetime
import tornado.ioloop
import json
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
        ('tls_cert', 'Enter path to a TLS certificate'),
        ('admin_user', 'Enter username for the first admin'),
        ('admin_pass', 'Enter password for the first admin')]
    values = {}
    for attr in attrs:
        name = attr[0]
        cmdhelp = attr[1]
        values[name] = getattr(args, name)
        if values[name] is None: # The CLI `args` doesn't have it, ask.
            values[name] = raw_input('%s: ' % cmdhelp)

    exception = None
    try:
        cli_info('Downloading Consul...')
        version = environment.install_consul()
        cli_success('Installed Consul %s' % version)
    except:
        exception = sys.exc_info()
    
    try:
        cli_info('Setting up the daemon...')
        environment.write_daemon_conf()
        environment.start_daemon()
    except OSError:
        exception = sys.exc_info()
    
    if exception:
        cli_error('Initialization failed because of one or more errors.')
        traceback.print_exception(*exception)
        sys.exit(1)
    else:
        from .api import login
        from . import datastore
        store = datastore.ConsulStore()
        run_sync = tornado.ioloop.IOLoop.instance().run_sync
        attempts, failed = 1, True
        cli_info('Waiting for the key value store to come alive...')
        while attempts <= environment.DATASTORE_ATTEMPTS:
            is_running = run_sync(store.check_connection)
            cli_info('  -> attempt #%i...' % attempts)
            if is_running:
                failed = False
                break
            else:
                time.sleep(environment.DATASTORE_RETRY_TIME)
                attempts+= 1
        if failed:
            cli_error('Store connection timeout after %i attempts.' \
                % attempts)
            sys.exit(1)
        else:
            # We have a connection, create an admin account
            create_admin = functools.partial(login.create_admin,
                store, values['admin_user'], values['admin_pass'])
            run_sync(create_admin)
            cli_success('Created first account. Setup is finished.')

def handle_stop(args):
    try:
        cli_info('Stopping the daemon...')
        environment.stop_daemon()
    except:
        cli_error('An exception occured during daemon stop process!')
        traceback.print_exc()

def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')
    subparsers = parser.add_subparsers(help='action')

    init_sub = subparsers.add_parser('init', help='Initializes and starts server')
    init_sub.add_argument('--tls-cert', help='Path to TLS certificate')
    init_sub.add_argument('--admin-user', help='Username of the first admin')
    init_sub.add_argument('--admin-pass', help='Password of the first admin')
    # args.sub will equal 'start' if this subparser is used
    init_sub.set_defaults(sub='init')
    
    stop_sub = subparsers.add_parser('stop', help='Stops the server')
    stop_sub.set_defaults(sub='stop')
    
    args = parser.parse_args()
    # Define handlers for each subparser
    handlers = {
        'init': handle_init,
        'stop': handle_stop
    }
    # Call the proper handler based on the subparser argument
    handlers[args.sub](args)
