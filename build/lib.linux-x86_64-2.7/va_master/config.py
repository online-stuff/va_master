import pkg_resources
import logging
import os
from . import deploy_handler
from . import datastore
from .host_drivers import openstack

def get_server_static():
    # get the server assets static path
    return pkg_resources.resource_filename('va_dashboard', 'static')

class Config(object):
    """A `Config` contains the configuration options for the whole master. It doesn't
    need explicit options and provides smart defaults."""

    def __init__(self, **kwargs):
        # Defaults first:
        self.version = (1, 0, 0)
        self.consul_port = 0
        self.datastore = datastore.ConsulStore()
        self.logger = logging.getLogger('deployer')
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('[%(asctime)-15s] %(message)s'))
        self.logger.addHandler(ch)
        self.server_port = 80
        self.server_static_path = get_server_static()
        self.deploy_pool_count = 3
        # Now dynamically inject any kwargs
        for kw in kwargs:
            setattr(self, kw, kwargs[kw])
        self.deploy_handler = deploy_handler.DeployHandler(self.datastore, self.deploy_pool_count)

    def pretty_version(self):
        return '.'.join([str(x) for x in self.version])
