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

from novaclient import client

PROVIDER_TEMPLATE = '''VAR_PROVIDER_NAME:
  auth_minion: VAR_THIS_IP
  minion:
    master: VAR_THIS_IP
    master_type: str
  # The name of the configuration profile to use on said minion
  ssh_key_name: VAR_SSH_NAME
  ssh_key_file: VAR_SSH_FILE
  ssh_interface: private_ips
  use_keystoneauth: True
  driver: nova
  user: VAR_USERNAME
  tenant: VAR_TENANT
  password: VAR_PASSWORD
  identity_url: VAR_IDENTITY_URL
  compute_region: VAR_REGION
  networks:
    - net-id: VAR_NETWORK_ID'''

PROFILE_TEMPLATE = '''VAR_PROFILE_NAME:
    provider: VAR_PROVIDER_NAME
    image: VAR_IMAGE
    size: VAR_SIZE
    securitygroups: VAR_SEC_GROUP
    minion:
        grains:
            role: VAR_ROLE
'''

class OpenStackDriver(base.DriverBase):
    def __init__(self, provider_name = 'openstack_provider', profile_name = 'openstack_profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master_key'):
        """ The standard issue init method. Borrows most of the functionality from the BaseDriver init method, but adds a self.regions attribute, specific for OpenStack hosts. """

        kwargs = {
            'driver_name' : 'openstack',
            'provider_template' : PROVIDER_TEMPLATE,
            'profile_template' : PROFILE_TEMPLATE,
            'provider_name' : provider_name,
            'profile_name' : profile_name,
            'host_ip' : host_ip,
            'key_name' : key_name,
            'key_path' : key_path
            }
        super(OpenStackDriver, self).__init__(**kwargs)

    @tornado.gen.coroutine
    def driver_id(self):
        """ Pretty simple. """
        raise tornado.gen.Return('openstack')

    @tornado.gen.coroutine
    def friendly_name(self):
        """ Pretty simple """
        raise tornado.gen.Return('OpenStack')

    @tornado.gen.coroutine
    def get_steps(self):
        """ Adds a host_ip, tenant and region field to the first step. These are needed in order to get OpenStack values. """

        steps = yield super(OpenStackDriver, self).get_steps()
        steps[0].add_fields([
            ('host_ip', 'Keystone host_ip:port (xx.xx.xxx.xx:35357)', 'str'),
            ('tenant', 'Tenant', 'str'),
            ('region', 'Region', 'options'),
        ])
        self.steps = steps
        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_networks(self):
        networks = ['list', 'of', 'networks']
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        sec_groups = ['list', 'of', 'security', 'groups']
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        images = ['list', 'of', 'images']
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        sizes = ['list', 'of', 'sizes']
        raise tornado.gen.Return(sizes)


    @tornado.gen.coroutine
    def get_instances(self, host):
        try:
            servers = []
            instances = [
                {
                    'hostname' : 'hostname', 
                    'ip' : 'ip', 
                    'size' : 'size',
                    'used_disk' : 'used_disk', 
                    'used_ram' : 'used_ram', 
                    'used_cpu' : 'used_cpu',
                    'status' : 'status', 
                    'host' : host['hostname'], 
                } for x in servers 
            ]
        except Exception as e: 
            print ('Cannot get instances. ')
            import traceback
            print traceback.print_exc()
            raise tornado.gen.Return([])
        raise tornado.gen.Return(instances)



    @tornado.gen.coroutine
    def get_host_status(self, host):
        """ Tries to get the token for the host. If not successful, returns an error message. """
        raise tornado.gen.Return(True)

    @tornado.gen.coroutine
    def get_host_data(self, host):
        """ Gets various data about the host and all the instances using the get_openstack_value() method. Returns the data in the same format as defined in the base driver. """
        try:
            limits = {
                'maxTotalCores' : 0, 
                'totalCoresUsed' : 0,
                'maxTotalRAMSize' : 0,  
                'totalRAMUsed' : 0, 
                'maxTotalVolumeGigabytes' : 0, 
                'totalGigabytesUsed' : 0, 
                'maxTotalInstances' : 0,
                'totalInstancesUsed' : 0
            }
        except Exception as e: 
            import traceback
            print traceback.print_exc()
            host_data = {
                'instances' : [],
                'limits' : {},
                'host_usage' : {},
                'status' : {'success' : False, 'message' : 'Could not connect to the libvirt host. ' + e.message}
            }
            raise tornado.gen.Return(host_data)


        instances = yield self.get_instances(host)

        host_usage = {
            'max_cpus' : limits['maxTotalCores'],
            'used_cpus' : limits['totalCoresUsed'], 
            'free_cpus' : limits['maxTotalCores'] - limits['totalCoresUsed'], 
            'max_ram' : limits['maxTotalRAMSize'], 
            'used_ram' : limits['totalRAMUsed'],
            'free_ram' : limits['maxTotalRAMSize'] - limits['totalRAMUsed'], 
            'max_disk' : tenant_limits['maxTotalVolumeGigabytes'], 
            'used_disk' : tenant_limits['totalGigabytesUsed'], 
            'free_disk' : tenant_limits['maxTotalVolumeGigabytes'] - tenant_limits['maxTotalVolumeGigabytes'],
            'max_instances' : limits['maxTotalInstances'], 
            'used_instances' : limits['totalInstancesUsed'], 
            'free_instances' : limits['maxTotalInstances'] - limits['totalInstancesUsed']
        }

        host_data = {
            'instances' : instances, 
            'host_usage' : host_usage,
            'status' : {'success' : True, 'message': ''}
        }
        raise tornado.gen.Return(host_data)


    @tornado.gen.coroutine
    def instance_action(self, host, instance_name, action):
        instance_action = {
            'delete' : 'delete_action',
            'reboot' : 'reboot_action',
            'start' : 'start_action',
            'stop' : 'stop_action',
            'suspend' : 'suspend_action',
            'resume' : 'resume_action,
        }
        raise tornado.gen.Return(True)



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
    	    raise tornado.gen.Return(StepResult(
        		errors=[], new_step_index=0, option_choices={'region' : self.regions,}
    	    ))
        elif step_index == 0:
    	    self.token_data = yield self.get_token(field_values)
            os_base_url = 'http://' + field_values['host_ip'] + '/v2.0'

            self.provider_vars['VAR_TENANT'] = field_values['tenant']
            self.provider_vars['VAR_IDENTITY_URL'] = os_base_url
            self.provider_vars['VAR_REGION'] = field_values['region']

        elif step_index == 1:
            for field in ['network', 'sec_group']:
                field_values[field] = field_values[field].split('|')[1]

        try:
            step_kwargs = yield super(OpenStackDriver, self).validate_field_values(step_index, field_values)
        except:
            import traceback
            traceback.print_exc()
        raise tornado.gen.Return(StepResult(**step_kwargs))


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
            yield super(OpenStackDriver, self).create_minion(host, data)
        except:
            import traceback
            traceback.print_exc()
