import json
import requests
import subprocess
import traceback
import tornado.gen
from host_drivers import openstack, aws, vcloud, libvirt_driver

from Crypto.PublicKey import RSA
from concurrent.futures import ProcessPoolExecutor


class DeployHandler(object):
    def __init__(self, datastore, deploy_pool_count):
        self.datastore = datastore
        self.datastore.insert('hosts', [])
        self.deploy_pool_count = deploy_pool_count
        self.pool = ProcessPoolExecutor(deploy_pool_count)
        self.drivers = [openstack.OpenStackDriver(), libvirt_driver.LibVirtDriver(), ]

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
            hosts = [{'name' : host['hostname'], 'driver' : host['driver_name'], 'is_deletable' : True} for host in hosts]
        except self.datastore.KeyNotFound:
            hosts = []
        raise tornado.gen.Return(hosts)

    @tornado.gen.coroutine
    def create_host(self, driver):
        try:
            new_hosts = yield self.datastore.get('hosts')
        except self.datastore.KeyNotFound:
            new_hosts = []
        print ('Old hosts are : ', new_hosts)
        print ('Field values are : ', driver.field_values)
        new_hosts.append(driver.field_values)
        print ('New hosts are : ', new_hosts)
        yield self.datastore.insert('hosts', new_hosts)

