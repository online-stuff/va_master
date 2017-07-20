import tornado
import functools
import pkg_resources
import logging
import os
from . import deploy_handler
from . import datastore

def get_server_static():
    # get the server assets static path
    return pkg_resources.resource_filename('va_dashboard', 'static')

# A global logger for any general use
logger = logging.getLogger('deployer')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('[%(asctime)-15s] %(message)s'))
logger.addHandler(ch)

class Config(object):
    """A `Config` contains the configuration options for the whole master. It doesn't
    need explicit options and provides smart defaults."""

    def __init__(self, **kwargs):
        # Defaults first:
        self.version = (1, 0, 0)
        self.consul_port = 0
        self.datastore = datastore.ConsulStore()
        self.logger = logger
        self.server_port = 80
        self.server_static_path = get_server_static()
        self.deploy_pool_count = 3
        self.ssh_key_path = '/root/.ssh/'
        self.ssh_key_name = 'va-master' 

        # Now dynamically inject any kwargs
        for kw in kwargs:
            setattr(self, kw, kwargs[kw])
        self.deploy_handler = deploy_handler.DeployHandler(self.datastore, self.deploy_pool_count, self.ssh_key_name, self.ssh_key_path)

    def init_handler(self, init_vals): 
        run_sync = tornado.ioloop.IOLoop.instance().run_sync
        init_vals = functools.partial(self.deploy_handler.init_vals, init_vals)
        run_sync(init_vals)

    def pretty_version(self):
        return '.'.join([str(x) for x in self.version])
