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
import json

# The template of running programs for Supervisor daemon
supervisor_template = '''[supervisord]
loglevel=debug

[program:saltmaster]
command=%(salt_master_path)s

[program:consul]
command=/usr/bin/consul agent -config-file=/etc/consul.json
startretries=1

[program:va_master]
command=%(python_path)s -m va_scheduler'''

def write_supervisor_conf():
    """Writes configuration file for Supervisor daemon."""
    paths = {
        'salt_master_path': distutils.spawn.find_executable('salt-master'),
        'python_path': sys.executable
    }
    supervisor_conf = supervisor_template % paths
    with open('/etc/supervisor/conf.d/supervisor_master.conf', 'w') as f:
        f.write(supervisor_conf)

def write_consul_conf(ip):
    """Writes configuration file for Consul server.
    Parameters:
      ip - The IP that Consul is going to advertise
    """
    json_conf = {
        'datacenter': 'dc1',
        'data_dir': '/usr/share/consul',
        'advertise_addr': ip,
        'bootstrap_expect': 1,
        'server': True
    }
    with open('/etc/consul.json', 'w') as f:
        json.dump(json_conf, f)

def reload_daemon():
    try:
        subprocess.check_call(['supervisorctl', 'reread'])
        subprocess.check_call(['supervisorctl', 'reload'])
        return True
    except:
        return False
