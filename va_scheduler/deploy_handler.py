import threading
import Queue
import json
import requests
import subprocess
import traceback
from concurrent.futures import ProcessPoolExecutor

class DeployHandler(object):
    def __init__(self, config):
        self.config = config
        self.pool = ProcessPoolExecutor(config.deploy_pool_count)

    def start(self):
        pass

    @tornado.gen.coroutine
    def get_drivers(self):
        raise tornado.gen.Return([
            host_drivers.openstack.OpenStackDriver()
        ])

    @tornado.gen.coroutine
    def get_driver_by_id(self, id_):
        drivers = yield self.get_drivers()
        for driver in drivers:
            yield driver_id = driver.driver_id()
            if driver_id == id_:
                raise tornado.gen.Return(driver)
        raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def list_hosts(self):
        try:
            hosts = yield self.config.datastore.get('hosts')
        except self.config.datastore.KeyNotFound:
            hosts = []
        raise tornado.gen.Return(hosts)

    @tornado.gen.coroutine
    def create_host(self, host_name, driver_id, field_values): # name, driver_name, salt_provider, salt_profile):
        try:
            new_hosts = yield self.config.datastore.get('hosts')
        except self.config.datastore.KeyNotFound:
            new_hosts = []
        driver = yield get_driver_by_id(driver_id)
        provider, profile = driver.get_salt_configs(field_values, )
        
        new_hosts.append({'name': name, 'salt_provider': salt_provider,
            'salt_profile': salt_profile, 'driver_name': driver_name})
        yield self.config.datastore.insert(new_hosts)
