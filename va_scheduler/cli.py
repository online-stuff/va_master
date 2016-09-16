from . import config, installer
from .api import login
from datetime import datetime
import json
import os
import sys
import argparse
import subprocess

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

def get_cli_config():
    """Get a valid `Config` that can be used during the CLI session."""
    # TODO: Use persistent config file
    return config.Config()

def handle_start(args):
    """Handles cli `start` command. Should write proper conf and start daemon."""
    attrs = [
        ('ip', 'Enter the IPv4 addr. of this machine'),
        ('admin_user', 'Enter username for the first admin'),
        ('admin_pass', 'Enter password for the first admin')]
    values = {}
    for attr in attrs:
        if getattr(args, attr[0]) is None:
            values[attr] = raw_input('%s: ' % attr[1])
        else:
            values[attr] = getattr(args, attr[0])

    if os.geteuid() != 0:
        cli_info('You are not running as root, going to interactively ask' + \
        ' for sudo.')
        has_sudo = os.path.isfile('/usr/bin/sudo')
        if not has_sudo:
            cli_error('Could not find `sudo` command in order to gain superuser' + \
            'priviliges. Try to install `sudo` and check if /usr/bin/sudo exists.')
            return
        else:
            this_executable = distutils.spawn.find_executable('vapourapps')
            try:
                subprocess.check_call('sudo', this_executable, 'pkgsetup', values['ip'])
            except:
                pass
    else:
        handle_pkgsetup(values['ip'])
    tries = 0
    while tries < 5:
        
def handle_pkgsetup(args):
    """Handles `pkginstall` command. This is always ran as root."""
    if os.geteuid() != 0:
        cli_error('pkgsetup needs root.')
        sys.exit(1)
    cli_info('Configuring Consul...')
    installer.conf_consul(args.ip)
    cli_info('Installing packages...')
    installer.install_pkgs()
    cli_info('Reloading daemon...')
    result = installer.reload_daemon()
    if not result:
        cli_error('Failed reloading the daemon, check supervisor logs.' + \
        '\nYou may try `service supervisor restart` or ' + \
        '/var/log/supervisor/supervisord.log')

def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')
    subparsers = parser.add_subparsers(help='action')

    init_sub = subparsers.add_parser('init', help='Set up VapourApps')
    init_sub.add_argument('--ip', help='The IP of this machine, which is ' + \
        'going to be advertised to apps')
    init_sub.add_argument('--admin-user', help='Username of the first admin')
    init_sub.add_argument('--admin-pass', help='Password of the first admin')
    # args.sub will equal 'start' if this subparser is used
    start_sub.set_defaults(sub='init')

    pkgsetup_sub = subparsers.add_parser('pkgsetup',
        help='Installs required APT packages and sets up configuration')
    pkgsetup_sub.add_argument('ip', help='IP address of this machine')
    pkgsetup_sub.set_defaults(sub='pkgsetup')

    stop_sub = subparsers.add_parser('stop', help='Stops the server')
    stop_sub.set_defaults(sub='stop')

    args = parser.parse_args()
    # Define handlers for each subparser
    handlers = {
        'init': handle_init,
        'pkgsetup': handle_pkgsetup,
        'stop': handle_stop
    }
    # Call the proper handler based on the subparser argument
    handlers[args.sub](args)
