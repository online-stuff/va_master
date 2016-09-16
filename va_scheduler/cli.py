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
        ('ip', 'Enter the IPv4 addr. of this machine'),
        ('admin_user', 'Enter username for the first admin'),
        ('admin_pass', 'Enter password for the first admin')]
    values = {}
    for attr in attrs:
        name = attr[0]
        cmdhelp = attr[1]
        values[name] = getattr(args, name)
        if values[name] is None:
            values[name] = raw_input('%s: ' % cmdhelp)
    if os.geteuid() != 0: # Not root, re-run the same thing with sudo
        cli_info('\n----\n[!] You are not running as root, going to interactively ask' + \
        ' for sudo.')
        has_sudo = os.path.isfile('/usr/bin/sudo')
        if not has_sudo:
            cli_error('Could not find `sudo` command in order to gain superuser' + \
            'priviliges. Try to install `sudo` and check if /usr/bin/sudo exists.')
            return
        else:
            this_executable = distutils.spawn.find_executable('vapourapps')
            # Note, `argparse` translates dashes('-') into underscores('_')
            # in order to be Pythonic
            this_args = [
                '--ip', values['ip'],
                '--admin-user', values['admin_user'],
                '--admin-pass', values['admin_pass']]
            try:
                subprocess.check_call(['sudo', this_executable, 'init'] + this_args)
            except:
                traceback.print_exc()
    else:
        result = True
        try:
            environment.write_supervisor_conf()
            cli_success('Configured Supervisor.')
        except:
            cli_error('Failed configuring Supervisor: ')
            traceback.print_exc()
            result = False
        try:
            environment.write_consul_conf(values['ip'])
            cli_success('Configured Consul.')
        except:
            cli_error('Failed configuring Consul: ')
            traceback.print_exc()
            result = False

        if not result:
            cli_error('Initialization failed because of one or more errors.')
        else:
            try:
                environment.reload_daemon()
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
            tries = 1
            failed = True
            cli_info('Waiting for the key value store to come alive...')
            while tries < 6:
                is_running = run_sync(store.check_connection)
                cli_info('  -> attempt #%i...' % tries)
                if is_running:
                    failed = False
                    break
                else:
                    time.sleep(5)
                    tries+= 1
            if failed:
                cli_error('Store connection timeout.')
            else:
                create_admin = functools.partial(login.create_admin,
                    store, values['admin_user'], values['admin_pass'])
                run_sync(create_admin)

def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')
    subparsers = parser.add_subparsers(help='action')

    init_sub = subparsers.add_parser('init', help='Set up VapourApps')
    init_sub.add_argument('--ip', help='The IP of this machine, which is ' + \
        'going to be advertised to apps')
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
        'stop': lambda x: None
    }
    # Call the proper handler based on the subparser argument
    handlers[args.sub](args)
