from distutils.core import setup
import sys
import os
import logging
import subprocess
import urllib
import zipfile
import tempfile

def install_deps():
    if os.geteuid() != 0:
        logging.error('The package must be installed as root.')
        sys.exit(1)

    consul_version = '0.6.4'
    consul_url = 'https://releases.hashicorp.com/consul/0.6.4/consul_%s_linux_amd64.zip' % consul_version
    f = tempfile.NamedTemporaryFile(delete=False)
    consul_zip_path = f.name
    f.close()
    urllib.URLopener().retrieve(consul_url, consul_zip_path)
    consul_zip = zipfile.ZipFile(consul_zip_path, 'r')
    consul_zip.extractall('/usr/bin')
    consul_zip.close()
    pkgs = ['supervisor', 'python-virtualenv', 'build-essential', 'python-dev',
        'libssl-dev', 'libffi-dev', 'libzmq-dev']
    try:
        subprocess.check_call(['apt-get', 'update'])
    except:
        logging.warning('apt-get update failed.')
    subprocess.check_call(['apt-get', 'install', '-y'] + pkgs)

install_deps()

setup(
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
