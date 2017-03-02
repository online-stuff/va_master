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
import json, yaml

from salt.client import Caller
import distutils.spawn

# Datastore connection retry time
DATASTORE_RETRY_TIME = 5
DATASTORE_ATTEMPTS = 5

# Supervisor configuration file path
SUPERVISOR_CONF_PATH = '/etc/supervisor/conf.d/va_scheduler.conf'
# Consul configuration file path
CONSUL_CONF_PATH = '/etc/consul.json'
# The template of running programs for Supervisor daemon
SUPERVISOR_TEMPLATE = '''[supervisord]
loglevel=debug

[program:saltmaster]
command=%(salt_master_path)s

[program:consul]
command=/usr/bin/consul agent -config-file=/etc/consul.json
startretries=1

[program:va_master]
command=%(python_path)s -m va_master'''

def write_vpn_pillar(vpn_domain):
    with open('/srv/pillar/credentials.sls', 'r') as f: 
        a = yaml.load(f.read())
        a['domain'] = vpn_domain
    with open('/srv/pillar/credentials.sls', 'w') as f: 
        f.write(yaml.dump(a, default_flow_style=False))


def run_vpn():
    salt_client = Caller()
    salt_client.cmd('state.highstate')    
        

def write_supervisor_conf():
    """Writes configuration file for Supervisor daemon."""
    paths = {
        'salt_master_path': distutils.spawn.find_executable('salt-master'),
        'python_path': sys.executable
    }
    supervisor_conf = SUPERVISOR_TEMPLATE % paths
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(supervisor_conf)
    subprocess.check_call(['mv', f.name, SUPERVISOR_CONF_PATH])

def write_consul_conf(ip):
    """Writes configuration file for Consul server.
    Parameters:
      ip - The IP that Consul is going to advertise
    """
    json_conf = {
        'datacenter': 'dc1',
        'data_dir': '/usr/share/consul',
#        'advertise_addr': ip,
        'advertise_addr': '127.0.0.1',
        'bootstrap_expect': 1,
        'server': True
    }
    with tempfile.NamedTemporaryFile(delete=False) as f:
        json.dump(json_conf, f)
    subprocess.check_call(['mv', f.name, CONSUL_CONF_PATH])

def reload_daemon():
    try:
        subprocess.check_call(['supervisorctl', 'reload'])
        return True
    except:
        return False
