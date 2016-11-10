import json
import requests
import subprocess
import traceback
from tornado.gen import coroutine, Return
import tornado.gen
from host_drivers import openstack, aws, vcloud, libvirt_driver

from Crypto.PublicKey import RSA
from concurrent.futures import ProcessPoolExecutor


class DeployHandler(object):
    """A `DeployHandler` manages all app deployments and host operations."""
    
    def __init__(self):
        self.datastore = None
        self.proc_count = -1
        self.pool = None

    def set_datastore(self, datastore, deploy_pool_count):
        self.datastore = datastore
#        self.datastore.insert('hosts', [])
        self.deploy_pool_count = deploy_pool_count
        self.pool = ProcessPoolExecutor(deploy_pool_count)
        self.drivers = [openstack.OpenStackDriver(), libvirt_driver.LibVirtDriver(), ]

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
        raise tornado.gen.Return(self.drivers)

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
            hosts = [{'name' : host['hostname'], 'driver' : host['driver_name'], 'is_deletable' : True} for host in hosts]
        except self.datastore.KeyNotFound:
            hosts = []
        raise Return(hosts)

    @tornado.gen.coroutine
    def create_host(self, driver):
        try:
            new_hosts = yield self.datastore.get('hosts')
        except self.datastore.KeyNotFound:
            new_hosts = []
        new_hosts.append(driver.field_values)
        yield self.datastore.insert('hosts', new_hosts)
