#!/usr/bin/env python
import argparse
import os
import sys
import subprocess
import shutil
import urllib
import json
import socket
import logging

def install():
    if os.geteuid() != 0:
        logging.error('This script must be ran as a root! Try `sudo ./install.py`')
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Installs the master')
    parser.add_argument('--consul-version', default='0.6.4')
    args = parser.parse_args()

    consul_url = 'https://releases.hashicorp.com/consul/0.6.4/consul_%s_linux_amd64.zip' % (args.consul_version)
    this_dir = os.path.dirname(__file__)
    consul_zip = os.path.abspath(os.path.join(this_dir, 'consul.zip'))
    consul_bin = os.path.abspath(os.path.join(this_dir, 'consul'))
    venv = os.path.abspath(os.path.join(this_dir, 'venv'))
    venv_pip = os.path.abspath(os.path.join(this_dir, 'venv', 'bin', 'pip'))
    requirements = os.path.abspath(os.path.join(this_dir, 'requirements.txt'))
    supervisor_conf_path = '/etc/supervisor/conf.d/supervisor_master.conf'
    supervisor_conf = '''[supervisord]
    loglevel = debug

    [program:saltmaster]
    command=/usr/lib/va_master/venv/bin/salt-master

    [program:consul]
    command = /usr/bin/consul agent -config-file=/etc/consul.json
    startretries = 1

    [program:va_master]
    command = /usr/lib/va_master/venv/bin/python /usr/lib/va_master/start.py'''
    consul_conf_path = '/etc/consul.json'
    consul_conf = {
        'datacenter': 'dc1',
        'data_dir': '/usr/share/consul',
        'advertise_addr': '%s',
        'bootstrap_expect': 1,
        'server': True
    }

    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

    def write_supervisor_conf():
        with open(supervisor_conf_path, 'w') as f:
            f.write(supervisor_conf)

    def write_consul_conf():
        with open(consul_conf_path, 'w') as f:
            consul_conf['advertise_addr'] %= get_ip()
            json.dump(consul_conf, f)

    pkgs = ['unzip', 'supervisor', 'python-virtualenv', 'build-essential', 'python-dev',
        'libssl-dev', 'libffi-dev']
    try:
        subprocess.check_call(['apt-get', 'update'])
    except:
        logging.warning('apt-get update failed.')

    subprocess.check_call(['apt-get', 'install', '-y'] + pkgs)
    write_consul_conf()
    write_supervisor_conf()
    urllib.URLopener().retrieve(consul_url, consul_zip)
    subprocess.check_call(['unzip', consul_zip])
    os.remove(consul_zip)
    shutil.move(consul_bin, '/usr/bin/consul')
    if os.path.isdir(venv):
        shutil.rmtree(venv)
    subprocess.check_call(['virtualenv', venv])
    subprocess.check_call([venv_pip, 'install', '-r', requirements])

if __name__ == '__main__':
    install()
