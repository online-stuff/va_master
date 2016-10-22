import distutils.spawn
import sys
import os
import stat
import logging
import subprocess
import urllib
import zipfile
import tempfile
import platform
import json
from StringIO import StringIO

# This module should contain functions for installing and configuring
# OS-specific packages, config files as well as environment constants. Those include:
# 
# * consul installation functions
# * daemon configuration files (upstart/systemd/...)


# Datastore connection retry time
DATASTORE_RETRY_TIME = 5
DATASTORE_ATTEMPTS = 5

CONSUL_VERSION = '0.7.0'

LINUX_CONSUL_ZIP = 'https://releases.hashicorp.com/consul/0.7.0/consul_0.7.0_linux_amd64.zip'
LINUX_MASTER_PATH = '/var/lib/va_master'
LINUX_SYSTEMD_TEMPLATE = '''
[Service]
ExecStart=%(python_path)s -m va_master
ExecStop=/usr/bin/python -c 'print()'
Restart=always
SyslogIdentifier=va_master

[Install]
WantedBy=multi-user.target'''
LINUX_SYSTEMD_PATH = '/etc/systemd/system/va_master.service'
LINUX_CONSUL_PATH = '/usr/bin/consul'

# `systemd` based daemon
def write_systemd_conf():
    """Writes configuration file for systemd"""
    paths = {
        #'salt_master_path': distutils.spawn.find_executable('salt-master'),
        'python_path': sys.executable
    }
    systemd_conf = LINUX_SYSTEMD_TEMPLATE % paths
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(systemd_conf)
    subprocess.check_call(['sudo', 'mv', f.name, LINUX_SYSTEMD_PATH])

def start_systemd():
    """Starts the daemon using systemd."""
    try:
        subprocess.check_call(['sudo', 'systemctl', 'enable', 'va_master'])
        subprocess.check_call(['sudo', 'systemctl', 'start', 'va_master'])
    except:
        raise OSError('Could not start daemon.')

def stop_systemd():
    """Stops the daemon using systemd."""
    try:
        subprocess.check_call(['sudo', 'systemctl', 'stop', 'va_master'])
    except:
        raise OSError('Could not stop daemon.')

# Functions regardless of init system type.
# TODO: Support upstart, systemV, ...

def get_supported_init_system():
    """Gets the supported init system (https://en.wikipedia.org/wiki/Init) by the
    current platform. 
    Returns:
        str: systemd|upstart
    """
    if not os.path.isdir('/etc/systemd'):
        raise OSError('Only systemd is supported at the moment.')
    return 'systemd'

def get_os():
    """Gets the operating system currently running.
    Returns:
        str: linux|windows
    """
    if platform.system() != 'Linux':
        raise OSError('Only GNU/Linux is supported at the moment.')
    return 'linux'

def write_daemon_conf():
    if get_supported_init_system() == 'systemd' and get_os() == 'linux':
        write_systemd_conf()

def start_daemon():
    if get_supported_init_system() == 'systemd' and get_os() == 'linux':
        start_systemd()

def stop_daemon():
    if get_supported_init_system() == 'systemd' and get_os() == 'linux':
        stop_systemd()

def install_consul():
    """Installs Consul by downloading it and unzipping it.
    Returns:
        str: Consul version"""
    if get_os() == 'linux':
        url = urllib.urlopen(LINUX_CONSUL_ZIP)
        zip = zipfile.ZipFile(StringIO(url.read()))
        consul_content = zip.read('consul')
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(consul_content)
        subprocess.check_call(['sudo', 'mv', f.name, LINUX_CONSUL_PATH])
        subprocess.check_call(['sudo', 'chmod', '+x', LINUX_CONSUL_PATH])
        return CONSUL_VERSION