import json
import requests
import subprocess
import traceback
import tornado.gen
from host_drivers import openstack, aws

from Crypto.PublicKey import RSA
from concurrent.futures import ProcessPoolExecutor


class DeployHandler(object):
    def __init__(self, datastore, deploy_pool_count):
        self.datastore = datastore
        self.deploy_pool_count = deploy_pool_count
        self.pool = ProcessPoolExecutor(deploy_pool_count)
        self.drivers = [openstack.OpenStackDriver(), aws.AWSDriver(),  ]


    def start(self):
        pass

    @tornado.gen.coroutine
    def create_ssh_keypair(self):
        pass

    @tornado.gen.coroutine
    def get_ssh_keypair(self):
        try:
            keydata = self.datastore.get('ssh_keypair')
        except self.datastore.KeyNotFound:
            # create new
            data = yield self.create_ssh_keypair()
            yield self.datastore.insert('ssh_keypair', data)
            raise tornado.gen.Return(data)
        raise tornado.gen.Return({'public': keydata['public'],
            'private': keydata['private']})

    @tornado.gen.coroutine
    def get_drivers(self):
        raise tornado.gen.Return(self.drivers)

    @tornado.gen.coroutine
    def get_driver_by_id(self, id_):
        drivers = yield self.get_drivers()
        for driver in drivers:
            driver_id = yield driver.driver_id()
            if driver_id == id_:
                raise tornado.gen.Return(driver)
        raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def list_hosts(self):
        try:
            hosts = yield self.datastore.get('hosts')
        except self.datastore.KeyNotFound:
            hosts = []
        raise tornado.gen.Return(hosts)

    @tornado.gen.coroutine
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
