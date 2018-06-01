import json, glob, yaml, datetime
import requests
import subprocess
import traceback
import functools
import tornado
import tornado.gen
from va_master.host_drivers import openstack, aws, vcloud, libvirt_driver, generic_driver, century_link, gce, vmware, digitalocean_driver, lxc

from Crypto.PublicKey import RSA
from concurrent.futures import ProcessPoolExecutor

from pbkdf2 import crypt


class DriversHandler(object):

    def __init__(self, datastore_handler, ssh_key_name, ssh_key_path, ssl_path):
        self.ssh_key_name = ssh_key_name
        self.ssh_key_path = ssh_key_path
        self.ssl_path = ssl_path
        self.datastore_handler = datastore_handler
        self.drivers = []

    @tornado.gen.coroutine
    def get_drivers(self):
        if not self.drivers: 
            init_vals = yield self.datastore_handler.get_init_vals()
            va_flavours = yield self.datastore_handler.datastore.get('va_flavours')
            host_ip =  init_vals['fqdn'] 

            kwargs = {
                'host_ip' : host_ip, 
                'key_name' : self.ssh_key_name, 
                'key_path' : self.ssh_key_path, 
                'datastore_handler' : self.datastore_handler,
            }
            self.drivers = [x(**kwargs) for x in [
                openstack.OpenStackDriver, 
                gce.GCEDriver,
                aws.AWSDriver,
                digitalocean_driver.DigitalOceanDriver

            ]]
           
            kwargs['flavours'] = va_flavours
            self.drivers += [x(**kwargs) for x in (
                century_link.CenturyLinkDriver, 
                libvirt_driver.LibVirtDriver,
                vmware.VMWareDriver,
                generic_driver.GenericDriver,
            )]

            kwargs['ssl_path'] = self.ssl_path
            self.drivers += [x(**kwargs) for x in (
                lxc.LXCDriver,
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

    #Designed to create sls files which will be used with various minion-specific data. Not used currently, and probably will need a states_handler.
    #Or just do this in the api/
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

