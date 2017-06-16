try: 
    from . import base
    from .base import Step, StepResult
except: 
    import base
    from base import Step, StepResult

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json
import subprocess
import os

from pyVmomi import vim
from pyVmomi import vmodl
from pyVim import connect

import ssl

#TODO remove this and work with actual certs. Or maybe have an option. 
ssl._create_default_https_context = ssl._create_unverified_context


PROVIDER_TEMPLATE = '''VAR_PROVIDER_NAME:
  driver: vmware
  user: 'VAR_USER'
  password: 'VAR_PASS'
  url: 'VAR_IP'
'''

PROFILE_TEMPLATE = '''VAR_PROFILE_NAME:
  provider: VAR_PROVIDER_NAME

  ## Optional arguments
  num_cpus: VAR_CPUS
  memory: VAR_MEMORYGB
  devices:
    cd:
      CD/DVD drive 1:
        device_type: datastore_iso
        iso
    disk:
      Hard disk 1:
        size: VAR_SIZE 
    network:
      Network adapter 1:
        name: 10.20.30-400-Test
        switch_type: standard
        ip: 10.20.30.123
        gateway: [10.20.30.110]
        subnet_mask: 255.255.255.128
        domain: example.com
    scsi:
      SCSI controller 1:
        type: lsilogic
    ide:
      IDE 2
      IDE 3

  domain: example.com
  dns_servers:
    - 123.127.255.240
    - 123.127.255.241
    - 123.127.255.242

  resourcepool: Resources
  cluster: Prod

  datastore: HUGE-DATASTORE-Cluster
  folder: Development
  datacenter: DC1
  host: c4212n-002.domain.com
  template: False
  power_on: True
  extra_config:
    mem.hotadd: 'yes'
    guestinfo.foo: bar
    guestinfo.domain: foobar.com
    guestinfo.customVariable: customValue
  annotation: Created by Salt-Cloud

  deploy: True
  customization: True
  private_key: /root/.ssh/mykey.pem
  ssh_username: cloud-user
  password: veryVeryBadPassword
  minion:
    master: 123.127.193.105

  file_map:
    /path/to/local/custom/script: /path/to/remote/script
    /path/to/local/file: /path/to/remote/file
    /srv/salt/yum/epel.repo: /etc/yum.repos.d/epel.repo

  hardware_version: 10
  image: centos64Guest

  #For Windows VM
  win_username: Administrator
  win_password: administrator
  win_organization_name: ABC-Corp
  plain_text: True
  win_installer: /root/Salt-Minion-2015.8.4-AMD64-Setup.exe
  win_user_fullname: Windows User'''

class VMWareDriver(base.DriverBase):
    def __init__(self, flavours, provider_name = 'vmware_provider', profile_name = 'vmware_profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore = None):
        """ The standard issue init method. Borrows most of the functionality from the BaseDriver init method, but adds a self.regions attribute, specific for VMWare hosts. """

        kwargs = {
            'driver_name' : 'vmware',
            'provider_template' : PROVIDER_TEMPLATE,
            'profile_template' : PROFILE_TEMPLATE,
            'provider_name' : provider_name,
            'profile_name' : profile_name,
            'host_ip' : host_ip,
            'key_name' : key_name,
            'key_path' : key_path, 
            'datastore' : datastore
            }
        self.flavours = flavours
        super(VMWareDriver, self).__init__(**kwargs)

    def get_datacenter(self, host):
        service_instance = connect.SmartConnect(host='10.10.3.10', user = 'root', port = 443, pwd = 'm33dicina', protocol = 'https')
        content = service_instance.RetrieveContent()
        datacenter = [x for x in content.rootFolder.childEntity if x.name == 'ha-datacenter'] or [None]
        return datacenter[0]

    @tornado.gen.coroutine
    def driver_id(self):
        """ Pretty simple. """
        raise tornado.gen.Return('vmware')

    @tornado.gen.coroutine
    def friendly_name(self):
        """ Pretty simple """
        raise tornado.gen.Return('VMWare')

    @tornado.gen.coroutine
    def get_steps(self):
        """ Works like the Base get_steps, but adds the host_ip and host_protocol fields. Also, there are no security groups in LibVirt, so that field is removed. """
        steps = yield super(VMWareDriver, self).get_steps()
        steps[0].add_fields([
            ('host_ip', 'Host ip', 'str'),
            ('port', 'Port', 'str'),            
            ('protocol', 'Protocol', 'str'),
        ])

        for i in range(3):
            del steps[1].fields[0]


        steps[1].add_fields([
            ('datacenter', 'Choose a datacenter from the list', 'options'),
        ])
#        datacenter = Step('Datacenter')
#        datacenter.add_fields([
#            ('datacenter', 'Choose a datacenter from the list', 'options'),
#        ])
#        steps[1] = datacenter

        print ('Steps are : ', [x.serialize() for x in steps])

        raise tornado.gen.Return(steps)


    @tornado.gen.coroutine
    def get_networks(self):
        networks = ['List', 'of', 'networks']
        #networks = pyvm.datacenter.get_networks()
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        sec_groups = ['List', 'of', 'security', 'groups']
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        images = [
            'EXCH201064.ISO',
            'SW_DVD5_Office_Professional_Plus_2010w_SP1_W32_English_CORE_MLF_X17-76748.ISO',
            'WIN7_32_64.iso',
            'Windows_Svr_DC_EE_SE_Web_2008R2_64-bit_English_X15-59754.ISO',
            'debian-7.8.0-amd64-netinst.iso',
            'debian-8.2.0-amd64-netinst.iso',
        ]
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        """ Gets the sizes using the get_openstack_value() method. """
        sizes = self.flavours.keys()
        raise tornado.gen.Return(sizes)


    @tornado.gen.coroutine
    def get_instances(self, host):
        """ Gets various information about the instances so it can be returned to host_data. The format of the data for each instance follows the same format as in the base driver description """

        service_instance = connect.SmartConnect(host=host['host_ip'], user = host['username'], port = int(host['port']), pwd = host['password'], protocol = host['protocol'])

        instances = []
        datacenter = self.get_datacenter(host)

        content = service_instance.RetrieveContent()
        vmFolder = datacenter.vmFolder
        vmList = vmFolder.childEntity
        for vm in vmList:
            print ('Instance is : ', {
                'hostname' : vm.name,
                'ip' : vm.guest.ipAddress ,
                'size' : 'va-small',
                'used_disk' : vm.summary.storage.committed,
                'used_ram' : vm.summary.quickStats.hostMemoryUsage,
                'used_cpu' : vm.summary.quickStats.overallCpuUsage,
                'status' : vm.overallStatus,
                'host' : host['hostname'],
            })

        for vm in vmList:
            instance = {
                'hostname' : vm.name, 
                'ip' : vm.guest.ipAddress , 
                'size' : 'va-small',
                'status' : vm.overallStatus, 
                'host' : host['hostname'], 
                'used_disk' :vm.summary.storage.committed,
                'used_ram' : vm.summary.quickStats.hostMemoryUsage, 
                'used_cpu' : vm.summary.quickStats.overallCpuUsage,
            }

            for key in [('used_disk', 2**30), ('used_ram', 2**20), ('used_cpu', 1)]: 
                instance[key[0]] = 0 if not instance[key[0]] else float(instance[key[0]]) / key[1]
            instances.append(instance)
        raise tornado.gen.Return(instances)



    @tornado.gen.coroutine
    def get_host_status(self, host):
        """ Tries to get the token for the host. If not successful, returns an error message. """
        try:
            service_instance = connect.SmartConnect(host=host['host_ip'], user = host['username'], port = int(host['port']), pwd = host['password'], protocol = host['protocol'])
        except Exception as e: 
            raise tornado.gen.Return({'success' : False, 'message' : e.message})

        raise tornado.gen.Return({'success' : True, 'message' : ''})

    @tornado.gen.coroutine
    def get_host_data(self, host, get_instances = True, get_billing = True):
        """ Gets various data about the host and all the instances using the get_openstack_value() method. Returns the data in the same format as defined in the base driver. """
        service_instance = connect.SmartConnect(host=host['host_ip'], user = host['username'], port = int(host['port']), pwd = host['password'], protocol = host['protocol'])

        if get_instances: 
            instances = yield self.get_instances(host)
        else: 
            instances = []

        datacenter = self.get_datacenter(host)

        host_usage = {
            'max_cpus' : 'n/a',
            'used_cpus' : sum([x['used_cpu'] for x in instances]), 
            'free_cpus' : 'n/a', 
            'max_ram' : 'n/a', 
            'used_ram' : sum([x['used_ram'] for x in instances]),
            'free_ram' : 'n/a', 
            'max_disk' : sum([x['used_disk'] + x['free_disk'] for x in instances]), 
            'used_disk' : sum([x['used_disk'] for x in instances]), 
            'free_disk' : sum([x['free_disk'] for x in instances]),
            'max_instances' : 'n/a', 
            'used_instances' : len(instances), 
            'free_instances' : 'n/a' 
        }

        host_data = {
            'instances' : instances, 
            'host_usage' : host_usage,
            'status' : {'success' : True, 'message': ''}
        }
        raise tornado.gen.Return(host_data)


    @tornado.gen.coroutine
    def instance_action(self, host, instance_name, action):
        """ Performs instance actions using a nova client. """
        raise tornado.gen.Return({'success' : True, 'message' : ''})



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        """ Uses the base driver method, but adds the region tenant and identity_url variables, used in the configurations. """
        options = {}
        if step_index < 0:
    	    raise tornado.gen.Return(StepResult(
        		errors=[], new_step_index=0, option_choices={}
    	    ))
        elif step_index == 0:
            self.provider_vars['VAR_IP'] = field_values['host_ip']
            self.provider_vars['VAR_USER'] = field_values['username']
            self.provider_vars['VAR_PASS'] = field_values['password']
            self.field_values['protocol'] = field_values['protocol']
            self.field_values['port'] = field_values['port']

            service_instance = connect.SmartConnect(host='10.10.3.10', user = 'root', port = 443, pwd = 'm33dicina', protocol = 'https')
            content = service_instance.RetrieveContent()
            datacenters = [x.name for x in content.rootFolder.childEntity]
            options = {'datacenter' : datacenters}
        elif step_index == 1: 
            self.field_values['datacenter'] = field_values['datacenter']
            field_values['sec_group'] = ''
            field_values['network'] = ''

        print ('CAlling step result with : ', step_index, field_values, options)
        step_result = yield super(VMWareDriver, self).validate_field_values(step_index, field_values, options = options)
        print ('Step result is : ', step_result.serialize())
        raise tornado.gen.Return(step_result)


    @tornado.gen.coroutine
    def create_minion(self, host, data):
        """ Works properly with the base driver method, but overwritten for bug tracking. """
        try:
#            nova = client.Client('2', host['username'], host['password'], host['tenant'], 'http://' + host['host_ip'] + '/v2.0')
#            full_key_path = host['salt_key_path'] + ('/' * host['salt_key_path'][-1] != '/') + host['salt_key_name'] + '.pub'
#            f = ''
#            with open(self.key_path + '.pub') as f: 
#                key = f.read()
#            keypair = nova.keypairs.create(name = self.key_name, public_key = key)
#            print ('Creating instance!')
            yield super(VMWareDriver, self).create_minion(host, data)
        except:
            import traceback
            traceback.print_exc()
