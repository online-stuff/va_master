import distutils
import sys
import os
import stat
import logging
import subprocess
import urllib
import zipfile
import tempfile
import platform


def debian_only(func):
    """A decorator that runs a function only for Debian-based distros."""
    allowed_distros = (('debian', 8.), ('ubuntu', 14.04))
    try:
        current_name = platform.linux_distribution()[0]
        current_version = float(platform.linux_distribution()[1])
    except:
        current_name = ''
        current_version = 0
    found = False
    for distro in allowed_distros:
        if distro[0].lower() == current_name.lower() and \
           distro[1] <= current_version:
            found = True
            break
    if found:
        return func
    else:
        logging.error(('Cannot continue installation because your OS(%s,%s) ' \
        + 'isn\'t supported. Currently supported are: %s') % \
        (current_name, current_version, repr(allowed_distros)))
        sys.exit(1)

@debian_only
def install_pkgs():
    """Installs Debian-specific packages that are required."""
    consul_version = '0.6.4'
    consul_url = 'https://releases.hashicorp.com/consul/0.6.4/consul_%s_linux_amd64.zip' % consul_version
    f = tempfile.NamedTemporaryFile(delete=False)
    consul_zip_path = f.name
    f.close()
    urllib.URLopener().retrieve(consul_url, consul_zip_path)
    consul_zip = zipfile.ZipFile(consul_zip_path, 'r')
    consul_zip.extractall('/usr/bin')
    consul_zip.close()
    os.chmod('/usr/bin/consul', st.st_mode | stat.S_IEXEC)

    pkgs = ['supervisor', 'python-virtualenv', 'build-essential', 'python-dev',
        'libssl-dev', 'libffi-dev', 'libzmq3', 'libzmq3-dev']
    try:
        subprocess.check_call(['apt-get', 'update'])
    except:
        logging.warning('apt-get update failed.')
    subprocess.check_call(['apt-get', 'install', '-y'] + pkgs)

    paths = {
        'salt_master_path': distutils.spawn.find_executable('salt-master'),
        'python_path': sys.executable
    }
    supervisor_conf = '''[supervisord]
loglevel=debug

[program:saltmaster]
command=%(salt_master_path)s

[program:consul]
command=/usr/bin/consul agent -config-file=/etc/consul.json
startretries=1

[program:va_master]
command=%(python_path)s -m va_scheduler''' % paths
    with open('/etc/supervisor/conf.d/supervisor_master.conf', 'w') as f:
        f.write(supervisor_conf)

def conf_consul(ip):
    json_conf = {
        'datacenter': 'dc1',
        'data_dir': '/usr/share/consul',
        'advertise_addr': ip,
        'bootstrap_expect': 1,
        'server': True
    }
    with open('/etc/consul.json', 'w') as f:
        json.dump(f, json_conf)

def reload_daemon():
    try:
        subprocess.check_call(['supervisorctl', 'reread'])
        subprocess.check_call(['supervisorctl', 'reload'])
        return True
    except:
        return False
