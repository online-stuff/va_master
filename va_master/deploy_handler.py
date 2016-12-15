import json, glob, yaml
import requests
import subprocess
import traceback
import functools
import tornado
import tornado.gen
from host_drivers import openstack, aws, vcloud, libvirt_driver


from Crypto.PublicKey import RSA
from concurrent.futures import ProcessPoolExecutor


class DeployHandler(object):
    def __init__(self, datastore, deploy_pool_count):
        self.datastore = datastore

        self.deploy_pool_count = deploy_pool_count
        self.pool = ProcessPoolExecutor(deploy_pool_count)


        
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
        hosts_ip = yield self.datastore.get('master_ip')
        libvirt_flavours = yield self.datastore.get('libvirt_flavours')
        salt_master_fqdn = yield self.datastore.get('salt_master_fqdn')


        self.drivers = [
            openstack.OpenStackDriver(host_ip = hosts_ip, key_name = 'va_master_key_name', key_path = '/root/va_master_key'), 
            libvirt_driver.LibVirtDriver(host_ip = hosts_ip, flavours = libvirt_flavours, salt_master_fqdn = salt_master_fqdn, key_name = 'va_master_key', key_path = '/root/va_master_key'), 
        ]

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
            for host in hosts: 
                driver = yield self.get_driver_by_id(host['driver_name'])
                host_status = yield driver.get_host_status(host)
                host['status'] = host_status
        except self.datastore.KeyNotFound:
            print ('No hosts found. ')
            hosts = []
        raise tornado.gen.Return(hosts)

    @tornado.gen.coroutine
    def create_host(self, driver):
        try:
            new_hosts = yield self.datastore.get('hosts')
        except self.datastore.KeyNotFound:
            new_hosts = []
        try: 
            new_hosts.append(driver.field_values)
            yield self.datastore.insert('hosts', new_hosts)
        except: 
            import traceback
            traceback.print_exc()

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
            except: 
                print ('error with ', state)
                import traceback
                traceback.print_exc()
        raise tornado.gen.Return(states_data)


    @tornado.gen.coroutine
    def get_states(self):
        try: 
            states_data = yield self.datastore.get('states')
        except self.datastore.KeyNotFound:
            states_data = yield self.get_states_data()
            yield self.datastore.insert('states', states_data)
        except: 
            import traceback
            traceback.print_exc()
        raise tornado.gen.Return(states_data)
    

    @tornado.gen.coroutine
    def reset_states(self):
        try: 
            yield self.datastore.delete('states')
            states_data = yield self.get_states_data()
            yield self.datastore.insert('states', states_data)
        except: 
            import traceback
            traceback.print_exc()


    @tornado.gen.coroutine
    def generate_top_sls(self):
        states = yield self.datastore.get('states')
        with open('/srv/salt/top.sls.base') as f: 
            current_top_sls = yaml.load(f.read())

        for state in states:
            print ('Adding state : ', state['name'])
            current_top_sls['base']['role:' + state['name']] = [{'match' : 'grain'}] + state['substates']
        try: 
            with open('/srv/salt/top.sls.tmp', 'w') as f:
                f.write(yaml.safe_dump(current_top_sls))
        except: 
            import traceback
            traceback.print_exc()

