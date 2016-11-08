from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json
import subprocess


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

class Driver(base.DriverBase):
    def __init__(self, provider_name = '_provider', profile_name = '_profile', host_ip = '192.168.80.39', key_name = 'openstack_key_name', key_path = '/root/openstack_key'):


        self.regions = ['RegionOne', ]
        super(OpenStackDriver, self).__init__(PROVIDER_TEMPLATE, PROFILE_TEMPLATE, provider_vars, profile_vars)


    @tornado.gen.coroutine
    def driver_id(self):
        raise tornado.gen.Return('openstack')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('OpenStack')

    @tornado.gen.coroutine
    def new_host_step_descriptions(self):
        raise tornado.gen.Return([
            {'name': 'Host info'},
            {'name': 'Pick a Network'},
            {'name': 'Security'}
        ])


#    These are defined in base.py but keeping them here until I make sure it works like this. 
#    @tornado.gen.coroutine
#    def get_salt_configs(self, skip_provider = False, skip_profile = False):
#        yield super(OpenStackDriver, self).get_salt_configs(skip_provider, skip_profile)
        

#    def write_salt_configs(self, skip_provider = False, skip_profile = False):
#        super(OpenStackDriver, self).get_salt_configs(skip_provider, skip_profile)

    @tornado.gen.coroutine
    def get_steps(self):
        host_info = Step('Host info')
        host_info.add_field('hostname', 'Name for the host', type = 'str')
        host_info.add_field('host_ip', 'Keystone host_ip:port (xx.xx.xxx.xx:35357)', type = 'str')
        host_info.add_field('username', 'Username', type = 'str')
        host_info.add_field('password', 'Password', type = 'str')
        host_info.add_field('tenant', 'Tenant', type = 'str')
        host_info.add_field('region', 'Region', type = 'options')


        net_sec = Step('Network & security group')
        net_sec.add_description_field('netsec_desc', 'Current connection info')
        net_sec.add_field('network', 'Pick network', type = 'options')
        net_sec.add_field('sec_group', 'Pick security group', type = 'options')


        imagesize = Step('Image & size')
        imagesize.add_field('image', 'Image', type = 'options')
        imagesize.add_field('size', 'Size', type = 'options')

        raise tornado.gen.Return([host_info, net_sec, imagesize])

    @tornado.gen.coroutine
    def get_token(self, field_values):
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
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices={'region' : self.regions,}
            ))

        elif step_index == 0:
            os_base_url = 'http://' + field_values['host_ip'] + '/v2.0'

            self.field_values['hostname'] = field_values['hostname']
            self.provider_vars['VAR_USERNAME'] = field_values['username']
            self.provider_vars['VAR_TENANT'] = field_values['tenant']
            self.provider_vars['VAR_PASSWORD'] = field_values['password']
            self.provider_vars['VAR_IDENTITY_URL'] = os_base_url
            self.provider_vars['VAR_REGION'] = field_values['region']


            networks = []
            self.token_data = yield self.get_token(field_values)

            networks = yield self.get_openstack_value(self.token_data, 'network', 'v2.0/networks')
            networks = ['%s | %s' % (x['name'], x['id']) for x in networks['networks']]

            sec_groups = yield self.get_openstack_value(self.token_data, 'compute', 'os-security-groups')

            self.field_values['sec_groups'] = sec_groups = ['%s | %s' % (x['name'], x['id']) for x in sec_groups['security_groups']]
            raise tornado.gen.Return(StepResult(errors=[], new_step_index=1,
                option_choices={
                    'network': networks,
                    'sec_group': sec_groups,
                }
            ))

        elif step_index == 1:
            self.provider_vars['VAR_NETWORK_ID'] = field_values['network'].split('|')[1]
            self.profile_vars['VAR_SEC_GROUP'] = field_values['sec_group'].split('|')[1]

            images = yield self.get_openstack_value(self.token_data, 'image', 'v2.0/images')
            images = images['images']
            self.field_values['images'] = images = [x['name'] for x in images]

            sizes = yield self.get_openstack_value(self.token_data, 'compute', 'flavors')
            sizes = sizes['flavors']
            self.field_values['sizes'] = sizes = [x['name'] for x in sizes]


 
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=2, option_choices={
                    'image': images,
                    'size': sizes,
                }
            ))
        else:
            self.profile_vars['VAR_IMAGE'] = field_values['image']
            self.profile_vars['VAR_SIZE'] = field_values['size']
 
            try:
                yield self.get_salt_configs(base_profile = True)
                yield self.write_configs()
            except:
                print ('Exception!')
                import traceback; traceback.print_exc()
                raise tornado.gen.Return([])


            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=-1, option_choices={}
            ))

