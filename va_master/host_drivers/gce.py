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
  # Set up the Project name and Service Account authorization
  project: VAR_PROJECT_ID 
  service_account_email_address: VAR_SERVICE_EMAIL 
  service_account_private_key: VAR_PATH_TO_PRIVATE_KEY

  # Set up the location of the salt master
  minion:
    master: VAR_THIS_IP

  # Set up grains information, which will be common for all nodes
  # using this provider
  grains:
    node_type: broker
    release: 1.0.1

  location: VAR_LOCATION 
  metadata: '{"sshKeys": "gceuser:VAR_PUB_KEY_CONTENTS"}'
  ssh_username: gceuser
  ssh_keyfile: VAR_SSH_FILE

  driver: gce
  ssh_interface: public_ips

  metadata: '{"one": "1", "2": "two", "sshKeys": "gceuser:VAR_PUB_KEY_CONTENTS"}'

  network: default
'''

PROFILE_TEMPLATE = '''VAR_PROFILE_NAME:
nino-gce-profile:
  use_persistent_disk: True
  delete_boot_pd: False
  deploy: True
  make_master: False
  provider: VAR_PROVIDER_NAME

  image: VAR_IMAGE
  size: VAR_SIZE
  minion:
      grains:
          role: VAR_ROLE
'''

class GGEDriver(base.DriverBase):
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
        self.regions = ['RegionOne', ]
        super(GGEDriver, self).__init__(**kwargs)

    @tornado.gen.coroutine
    def driver_id(self):
        """ Pretty simple. """
        raise tornado.gen.Return('gce')

    @tornado.gen.coroutine
    def friendly_name(self):
        """ Pretty simple """
        raise tornado.gen.Return('Google Cloud Engine')



    @tornado.gen.coroutine
    def get_steps(self):
        """ Adds a host_ip, tenant and region field to the first step. These are needed in order to get OpenStack values. """

        steps = yield super(GGEDriver, self).get_steps()
        steps[0].add_fields([
            ('host_ip', 'Keystone host_ip:port (xx.xx.xxx.xx:35357)', 'str'),
            ('tenant', 'Tenant', 'str'),
            ('region', 'Region', 'options'),
        ])
        self.steps = steps
        raise tornado.gen.Return(steps)


    @tornado.gen.coroutine
    def get_networks(self):
#        """ Gets the networks using the get_openstack_value() method. """
        networks = ['list', 'of', 'networks']
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
#        """ Gets the security groups using the get_openstack_value() method. """
        sec_groups = ['list', 'of', 'groups']
        raise tornado.gen.Return(sec_groups)

#    @tornado.gen.coroutine
#    def get_images(self):
#        """ Gets the images using the get_openstack_value() method. """
#        images = yield super(GGEDriver, self).get_images()
#        images = [x['name'] for x in images]
#        raise tornado.gen.Return(images)
#
#    @tornado.gen.coroutine
#    def get_sizes(self):
#        """ Gets the sizes using the get_openstack_value() method. """
#        sizes = yield self.get_openstack_value(self.token_data, 'compute', 'flavors')
#        sizes = [x['name'] for x in sizes['flavors']]
#        raise tornado.gen.Return(sizes)


    @tornado.gen.coroutine
    def get_instances(self, host):
        """ Gets various information about the instances so it can be returned to host_data. The format of the data for each instance follows the same format as in the base driver description """
        try:
            self.token_data = yield self.get_token(host)

            flavors = yield self.get_openstack_value(self.token_data, 'compute', 'flavors/detail')
            flavors = flavors['flavors']

            servers = yield self.get_openstack_value(self.token_data, 'compute', 'servers/detail')
            servers = servers['servers']

            tenants = yield self.get_openstack_value(self.token_data, 'identity', 'tenants')
            tenant = [x for x in tenants['tenants'] if x['name'] == host['tenant']][0]

            tenant_id = tenant['id']
            tenant_usage = yield self.get_openstack_value(self.token_data, 'compute', 'os-simple-tenant-usage/' + tenant_id)

            tenant_usage = tenant_usage['tenant_usage']
            instances = [
                {
                    'hostname' : x['name'], 
                    'ip' : x['addresses'].get('private', x['addresses'].get('public', [{'addr':'n/a'}]))[0]['addr'], #[x['addresses'].keys()[0]], 
                    'size' : f['name'],
                    'used_disk' : y['local_gb'], 
                    'used_ram' : y['memory_mb'], 
                    'used_cpu' : y['vcpus'],
                    'status' : x['status'], 
                    'host' : host['hostname'], 
                } for x in servers for y in tenant_usage['server_usages'] for f in flavors if y['name'] == x['name'] and f['id'] == x['flavor']['id']
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
        try:
            self.token_data = yield self.get_token(host)
        except Exception as e:
            raise tornado.gen.Return({'success' : False, 'message' : 'Error connecting to libvirt host. ' + e.message})

        raise tornado.gen.Return({'success' : True, 'message' : ''})

    @tornado.gen.coroutine
    def get_host_data(self, host):
        """ Gets various data about the host and all the instances using the get_openstack_value() method. Returns the data in the same format as defined in the base driver. """
        import time
        print ('Starting timer for OpenStack. ')
        t0 = time.time()
        try:
            self.token_data = yield self.get_token(host)

            tenants = yield self.get_openstack_value(self.token_data, 'identity', 'tenants')
            tenant = [x for x in tenants['tenants'] if x['name'] == host['tenant']][0]

            tenant_id = tenant['id']

            limits = yield self.get_openstack_value(self.token_data, 'compute', 'limits')
            tenant_limits = yield self.get_openstack_value(self.token_data, 'volumev2', 'limits')

            limits = limits['limits']['absolute']
            tenant_limits = tenant_limits['limits']['absolute']
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
        print ('Timer for OpenStack is : ', time.time() - t0)
        raise tornado.gen.Return(host_data)


    @tornado.gen.coroutine
    def instance_action(self, host, instance_name, action):
        """ Performs instance actions using a nova client. """
        try:
            nova = client.Client('2.0', host['username'], host['password'], host['tenant'], 'http://' + host['host_ip'] + '/v2.0')
            instance = [x for x in nova.servers.list() if x.name == instance_name][0]
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise tornado.gen.Return({'success' : False, 'message' : 'Could not get instance. ' + e.message})
        try:
            success = getattr(instance, action)()
            print ('Made action : ', success)
        except Exception as e:
            raise tornado.gen.Return({'success' : False, 'message' : 'Action was not performed. ' + e.message})

        raise tornado.gen.Return({'success' : True, 'message' : ''})



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        """ Uses the base driver method, but adds the region tenant and identity_url variables, used in the configurations. """
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
            step_kwargs = yield super(GGEDriver, self).validate_field_values(step_index, field_values)
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
            yield super(GGEDriver, self).create_minion(host, data)
        except:
            import traceback
            traceback.print_exc()
