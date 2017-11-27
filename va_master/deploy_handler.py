import json, glob, yaml, datetime
import requests
import subprocess
import traceback
import functools
import tornado
import tornado.gen
from host_drivers import openstack, aws, vcloud, libvirt_driver, generic_driver, century_link, gce, vmware

from va_master.consul_kv.datastore_handler import DatastoreHandler
from Crypto.PublicKey import RSA
from concurrent.futures import ProcessPoolExecutor

from pbkdf2 import crypt


class DeployHandler(object):

    executor = ProcessPoolExecutor(1)

    def __init__(self, datastore, deploy_pool_count, ssh_key_name, ssh_key_path):
        self.ssh_key_name = ssh_key_name
        self.ssh_key_path = ssh_key_path
        self.datastore = datastore

        self.datastore_handler = DatastoreHandler(datastore = self.datastore, datastore_spec_path = '/opt/va_master/consul_spec.json')
        self.drivers = []

        self.deploy_pool_count = deploy_pool_count
        self.executor = ProcessPoolExecutor(deploy_pool_count) 

    @tornado.gen.coroutine
    def init_vals(self, store, **kwargs):
        init_vars = {
            'va_flavours' : 'va_flavours', 
        }
        try: 
            store_values = yield self.datastore.get('init_vals')
        except:
            store_values = {}
            print ('No store values found - probably initializing deploy_handler for the first time. Will initialize with cli arguments. ')

        for var in init_vars: 
            if var in kwargs: 
                setattr(self, var, kwargs[var])
            else: 
                if var in store_values: 
                    setattr(self, var, store_values[var])
                else:
                    print ("Variable '%s' defined neither in store nor in arguments and will not be set in deploy handler. This may result with further errors. " % (var))


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
        if not self.drivers: 
            init_vals = yield self.datastore.get('init_vals')
            host_ip =  init_vals['fqdn'] 
            va_flavours = init_vals['va_flavours']

            kwargs = {
                'host_ip' : host_ip, 
                'key_name' : self.ssh_key_name, 
                'key_path' : self.ssh_key_path, 
                'datastore' : self.datastore
            }

            self.drivers = [x(**kwargs) for x in [
                openstack.OpenStackDriver, 
                gce.GCEDriver,
                generic_driver.GenericDriver,
                aws.AWSDriver,
            ]]
            kwargs['flavours'] = va_flavours


            self.drivers += [x(**kwargs) for x in (
                century_link.CenturyLinkDriver, 
                libvirt_driver.LibVirtDriver,
                vmware.VMWareDriver
            )]

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
    def get_provider_and_driver(self, provider_name = ''):
        if provider_name: 
            provider = yield self.get_provider(provider_name)
            driver = yield self.get_driver_by_id(provider['driver_name'])
        else: 
            provider = yield self.get_provider('va_standalone_servers') 
            driver = yield self.get_driver_by_id('generic_driver')

        raise tornado.gen.Return((provider, driver))

    @tornado.gen.coroutine
    def get_standalone_provider(self):
        provider = yield self.datastore_handler.get_provider('va_standalone_servers')
        driver = yield self.get_driver_by_id('generic_driver')

        provider['servers'] = yield driver.get_servers(provider)

        provider['provider_name'] = ''
        for x in provider['servers']: 
            x['provider'] = ''

        raise tornado.gen.Return(provider)


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

    @tornado.gen.coroutine
    def store_action(self, user, path, data):
        try: 
            actions = yield self.datastore.get('actions')
        except: 
            actions = []
        actions.append({
            'username' : user['username'], 
            'type' : user['type'], 
            'path' : path, 
            'data' : str(data), 
            'time' : str(datetime.datetime.now())
        })
        yield self.datastore.insert('actions', actions)

    @tornado.gen.coroutine
    def get_actions(self, number_actions, filters = {}):
        all_actions = yield self.datastore.get('actions')
        actions = all_actions[:number_actions] if number_actions else all_actions
        raise tornado.gen.Return(all_actions[:number_actions])


