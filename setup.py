import setuptools
import os
import sys
import tempfile
import subprocess
import stat
import subprocess
import logging
import zipfile
import urllib
import tempfile

# It is *strongly* recommended not to run any Python or modify the system
# during setup.py/pip installation and we are following that rule.
# However, if osdeps=1 all required OS *-dev packages are installed for easier
# deployment.

def find_exe(program):
    """Returns executable location, based on PATH and cwd."""
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath and is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path.strip('"'), program)
            if is_exe(exe_file):
                return exe_file
    return None

def install_osdeps():
    """Installs OS dependencies needed for Python libraries. Should not be
    ran by default."""

    # TODO: Support non-Debian distros like Fedora/RHEL
    subprocess.call(['echo', 'Trying to install OS dependencies, run without ' + \
    '`osdeps=1` if you want to skip this phase.\n'])
    for exe in ['sudo', 'apt-get', 'chmod', 'mv']:
        if find_exe(exe) is None:
            subprocess.call(['echo', ('[!] WARNING: Could not find ``%s`' + \
            ' command. Skipping OS dependency install phase.') % exe])
            return
    consul_version = '0.6.4'
    consul_url = 'https://releases.hashicorp.com/consul/0.6.4/consul_%s_linux_amd64.zip' % consul_version
    consul_zip_path = tempfile.mkstemp()[1]
    consul_exe_path = tempfile.mkstemp()[1]

    urllib.URLopener().retrieve(consul_url, consul_zip_path)
    consul_zip = zipfile.ZipFile(consul_zip_path, 'r')
    consul_zip.extract('consul', consul_exe_path)
    consul_zip.close()

    pkgs = ['supervisor', 'python-virtualenv', 'build-essential', 'python-dev',
        'libssl-dev', 'libffi-dev', 'libzmq3', 'libzmq3-dev']
    try:
        subprocess.check_call(['sudo', 'apt-get', 'update'])
    except:
        logging.warning('apt-get update failed.')
    subprocess.check_call(['sudo', 'apt-get', 'install', '-y'] + pkgs)
    subprocess.check_call(['sudo', 'mv', consul_exe_path, '/usr/bin/consul'])
    subprocess.check_call(['sudo', 'chmod', '+x', '/usr/bin/consul'])

if os.environ.get('osdeps', '') == '1':
    install_osdeps()

setuptools.setup(
  name='vapourapps',
  packages=['va_scheduler'],
  version='0.0.1',
  description='This package contains the master server of VapourApps, a DevOps tool for corporate apps.',
  keywords=['vapourapps'],
  author='Filip Dimitrovski',
  install_requires=[
    'tornado',
    'salt',
    'apache-libcloud',
    'python-novaclient',
    'pbkdf2'
  ],
  zip_safe=False,
  entry_points = {
    'console_scripts': [
        'vapourapps = va_scheduler.cli:entry'
    ]
  }
)
