import config, cli_environment
from api import login
from datetime import datetime
import tornado.ioloop
import yaml, json, glob
import os
import sys
import time
import argparse
import subprocess
import distutils
import traceback
import functools
import pkgutil

consul_conf_path = '/etc/consul.json'

def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')
    # Note: Every action subparser should have a `sub` property,
    # indicating its type. 
    subparsers = parser.add_subparsers(help='action')
    
    start = subparsers.add_parser('start')
    start.set_defaults(sub='start')

    p = os.path.join(os.path.dirname(__file__), 'api')
    print list(pkgutil.iter_modules([p]))
    args = parser.parse_args()
    print(args.sub)
if __name__ == '__main__': 
    entry()