import json, glob, yaml
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
        hosts_ip = self.datastore.get('ip_adress')
#        self.datastore.insert('hosts', [])
        self.deploy_pool_count = deploy_pool_count
        self.pool = ProcessPoolExecutor(deploy_pool_count)
        self.drivers = [openstack.OpenStackDriver(host_ip = hosts_ip), libvirt_driver.LibVirtDriver(host_ip = hosts_ip), ]

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
        new_hosts.append(driver.field_values)
        yield self.datastore.insert('hosts', new_hosts)

    @tornado.gen.coroutine
    def get_states_data(self):
        states_data = []
        subdirs = glob.glob('/srv/salt/*')
        for state in subdirs:
            try: 
                with open(state + '/appinfo.json') as f: 
                    states_data.append(json.loads(f.read()))
            except IOError as e: 
                print (state, ' does not have an appinfo file, skipping. ')
        raise tornado.gen.Return(states_data)

    @tornado.gen.coroutine
    def get_states(self):
        try: 
#            yield self.datastore.delete('states')
            states_data = yield self.datastore.get('states')
        except self.datastore.KeyNotFound:
            states_data = yield self.get_states_data()
            yield self.datastore.insert('states', states_data)
        except: 
            import traceback
            traceback.print_exc()
        raise tornado.gen.Return(states_data)
    
    @tornado.gen.coroutine
    def generate_top_sls(self):
        states = yield self.datastore.get('states')
        with open('/srv/salt/top.sls.base') as f: 
            current_top_sls = f.read()

        for state in states:
            current_top_sls += "\n  'role:'" + state['name'] + ":\n    - match: grain\n"

        with open('/srv/salt/top.sls.tmp', 'w') as f:
            f.write(current_top_sls)

