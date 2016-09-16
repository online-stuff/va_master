import setuptools
import os
import sys
import tempfile
import subprocess

# It is *strongly* recommended not to run any Python or modify the system
# during setup.py/pip installation and we are following that rule.
# However, if osdeps=1 all required OS *-dev packages are installed for easier
# deployment.

osdeps_script = '''
import stat, subprocess, logging, zipfile, urllib, tempfile, os
consul_version = '0.6.4'
consul_url = 'https://releases.hashicorp.com/consul/0.6.4/consul_%s_linux_amd64.zip' % consul_version
consul_zip_path = tempfile.mkstemp()[1]
urllib.URLopener().retrieve(consul_url, consul_zip_path)
consul_zip = zipfile.ZipFile(consul_zip_path, 'r')
consul_zip.extractall('/usr/bin')
consul_zip.close()
os.chmod('/usr/bin/consul', os.stat('/usr/bin/consul').st_mode | stat.S_IEXEC)

pkgs = ['supervisor', 'python-virtualenv', 'build-essential', 'python-dev',
    'libssl-dev', 'libffi-dev', 'libzmq3', 'libzmq3-dev']
try:
    subprocess.check_call(['apt-get', 'update'])
except:
    logging.warning('apt-get update failed.')
subprocess.check_call(['apt-get', 'install', '-y'] + pkgs)'''

def install_osdeps():
    subprocess.call(['echo', 'Trying to install OS dependencies, run without ' + \
    '`osdeps=1` if you want to skip this phase.\n'])
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(osdeps_script)
    args = [sys.executable, f.name]
    if os.geteuid() != 0:
        subprocess.call(['echo', 'Interactively asking for root permissions...\n'])
        has_sudo = os.path.isfile('/usr/bin/sudo')
        if not has_sudo:
            subprocess.call(['echo', 'Could not find `sudo` command in order to gain superuser' + \
            'priviliges. Try to install `sudo` and check if /usr/bin/sudo exists.\n'])
            sys.exit(1)
        else:
            args = ['/usr/bin/sudo'] + args
    subprocess.check_call(args)
    os.remove(f.name)

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
