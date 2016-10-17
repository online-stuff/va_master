import json
import requests
import subprocess
import traceback
from tornado.gen import coroutine, Return
from . import host_drivers
from Crypto.PublicKey import RSA
from concurrent.futures import ProcessPoolExecutor


class DeployHandler(object):
    """A `DeployHandler` manages all app deployments and host operations."""
    
    def __init__(self):
        self.datastore = None
        self.proc_count = -1
        self.pool = None

    def set_datastore(self, datastore):
        self.datastore = datastore

    def set_proc_count(self, proc_count):
        self.proc_count = proc_count
        self.pool = ProcessPoolExecutor(proc_count)

    def start(self):
        pass

    @coroutine
    def create_ssh_keypair(self):
        pass

    @coroutine
    def get_ssh_keypair(self):
        try:
            keydata = self.datastore.get('ssh_keypair')
        except self.datastore.KeyNotFound:
            # create new
            data = yield self.create_ssh_keypair()
            yield self.datastore.insert('ssh_keypair', data)
            raise Return(data)
        raise tornado.gen.Return({'public': keydata['public'],
            'private': keydata['private']})

    @coroutine
    def get_drivers(self):
        raise Return([
            host_drivers.openstack.OpenStackDriver()
        ])

    @coroutine
    def get_driver_by_id(self, id_):
        drivers = yield self.get_drivers()
        for driver in drivers:
            driver_id = yield driver.driver_id()
            if driver_id == id_:
                raise Return(driver)
        raise tornado.gen.Return(None)

    @coroutine
    def list_hosts(self):
        try:
            hosts = yield self.datastore.get('hosts')
        except self.datastore.KeyNotFound:
            hosts = []
        raise Return(hosts)

    @coroutine
    def create_host(self, host_name, driver_id, field_values): # name, driver_name, salt_provider, salt_profile):
        try:
            new_hosts = yield self.datastore.get('hosts')
        except self.datastore.KeyNotFound:
            new_hosts = []
        driver = yield self.get_driver_by_id(driver_id)
        provider, profile = driver.get_salt_configs(field_values, )

        new_hosts.append({'name': name, 'salt_provider': salt_provider,
            'salt_profile': salt_profile, 'driver_name': driver_name})
        yield self.datastore.insert(new_hosts)
