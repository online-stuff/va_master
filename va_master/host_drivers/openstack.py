from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json
import subprocess
import os

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from salt.cloud.clouds import nova

PROVIDER_TEMPLATE = '''VAR_PROVIDER_NAME:
  auth_minion: VAR_THIS_IP
  minion:
    master: VAR_THIS_IP
    master_type: str
  # The name of the configuration profile to use on said minion
  ssh_key_name: VAR_SSH_NAME
  ssh_key_file: VAR_SSH_FILE
  ssh_interface: private_ips
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
        super(OpenStackDriver, self).__init__(**kwargs) 

    @tornado.gen.coroutine
    def driver_id(self):
        raise tornado.gen.Return('openstack')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('OpenStack')


    @tornado.gen.coroutine
    def export_env_variables(self, username, tenant, url, password):
        os.environ['OS_USERNAME'] = self.provider_vars['VAR_USERNAME']
        os.environ['OS_PROJECT_NAME'] = self.provider_vars['VAR_TENANT']
        os.environ['OS_AUTH_URL'] = self.provider_vars['VAR_IDENTITY_URL']
        os.environ['PASSWORD'] = self.provider_vars['VAR_PASSWORD']
       
    @tornado.gen.coroutine
    def get_steps(self):
        steps = yield super(OpenStackDriver, self).get_steps()
        steps[0].add_fields([
            ('host_ip', 'Keystone host_ip:port (xx.xx.xxx.xx:35357)', 'str'),
            ('tenant', 'Tenant', 'str'),
            ('region', 'Region', 'options'),
        ])
        self.steps = steps
        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_token(self, field_values):
        print ('Field values are : ', field_values.keys())
        host, username, password, tenant = (field_values['host_ip'],
            field_values['username'], field_values['password'],
            field_values['tenant'])
        url = 'http://%s/v2.0/tokens' % host
        data = {
            'auth': {
                'tenantName': tenant,
                'passwordCredentials': {
                    'username': username,
                    'password': password
                }
            }
        }
        req = HTTPRequest(url, 'POST', body=json.dumps(data), headers={
            'Content-Type': 'application/json'
        })
        try:
            resp = yield self.client.fetch(req)
        except:
            import traceback
            traceback.print_exc()
            raise tornado.gen.Return((None, None))
        body = json.loads(resp.body)
        token = body['access']['token']['id']
        services = {}
        for serv in body['access']['serviceCatalog']:
            for endpoint in serv['endpoints']:
                if 'publicURL' not in endpoint: continue
                services[serv['type']] = endpoint['publicURL']
        raise tornado.gen.Return((token, services))


    @tornado.gen.coroutine
    def get_openstack_value(self, token_data, token_value, url_endpoint):
        url = token_data[1][token_value]
        req = HTTPRequest('%s/%s' % (url, url_endpoint), 'GET', headers={
            'X-Auth-Token': token_data[0],
            'Accept': 'application/json'
        })
        try:
            resp = yield self.client.fetch(req)
        except:
            print ('Exception!')
            import traceback; traceback.print_exc()
            raise tornado.gen.Return([])

        result = json.loads(resp.body)
        raise tornado.gen.Return(result)


    @tornado.gen.coroutine
    def get_networks(self):
        networks = yield self.get_openstack_value(self.token_data, 'network', 'v2.0/networks')
        networks = ['|'.join([x['name'], x['id']]) for x in networks['networks']]
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
       	sec_groups = yield self.get_openstack_value(self.token_data, 'compute', 'os-security-groups')
	sec_groups = ['|'.join([x['name'], x['id']]) for x in sec_groups['security_groups']]
	raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        images = yield self.get_openstack_value(self.token_data, 'image', 'v2.0/images')
        images = [x['name'] for x in images['images']]
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        sizes = yield self.get_openstack_value(self.token_data, 'compute', 'flavors')
        sizes = [x['name'] for x in sizes['flavors']]
        raise tornado.gen.Return(sizes)


    @tornado.gen.coroutine
    def get_host_data(self, host):
        try: 
            self.token_data = yield self.get_token(host)

            instances = yield self.get_openstack_value(self.token_data, 'compute', 'servers')
            instances = [x['name'] for x in instances['servers']]

            limits = yield self.get_openstack_value(self.token_data, 'compute', 'limits')

            host_data = {
                'instances' : instances, 
                'limits' : limits['limits'],
            }
        except:
            import traceback
            print ('There was an error reaching host: ', host['hostname'])
            traceback.print_exc()
            raise tornado.gen.Return({})

        raise tornado.gen.Return(host_data)



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
    	    raise tornado.gen.Return(StepResult(
        		errors=[], new_step_index=0, option_choices={'region' : self.regions,}
    	    ))
        elif step_index == 0:
    	    self.token_data = yield self.get_token(field_values)
    
    	    self.field_values['networks'] = yield self.get_networks() 
            self.field_values['sec_groups'] = yield self.get_sec_groups()
            self.field_values['images'] = yield self.get_images()
            self.field_values['sizes']= yield self.get_sizes()
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
        try:
            yield super(OpenStackDriver, self).create_minion(host, data)
        except: 
            import traceback
            traceback.print_exc()
