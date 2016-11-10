from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json

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
    securitygroups: VAR_SEC_GROUP'''

class OpenStackDriver(base.DriverBase):
    def __init__(self):
        self.client = AsyncHTTPClient()

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

    @tornado.gen.coroutine
    def get_salt_configs(self, field_values, provider_name, profile_name):
        provider = ''
        profile = ''

        return (provider, profile)

    @tornado.gen.coroutine
    def get_steps(self):
        host_info = Step('Host info')
        host_info.add_str_field('hostname', 'Keystone hostname:port (xx.xx.xxx.xx:35357)')
        host_info.add_str_field('username', 'Username')
        host_info.add_str_field('password', 'Password')
        host_info.add_str_field('tenant', 'Tenant')

        net_sec = Step('Network & security group')
        net_sec.add_description_field('netsec_desc', 'Current connection info')
        net_sec.add_options_field('network', 'Pick network')
        net_sec.add_options_field('sec_group', 'Pick security group')

        ssh = Step('SSH key')
        ssh.add_description_field('ssh_desc', 'Import this keypair into Openstack')
        ssh.add_str_field('private_key_name', 'Name of key')

        imagesize = Step('Image & size')
        imagesize.add_options_field('image', 'Image')
        imagesize.add_options_field('size', 'Size')
        raise tornado.gen.Return([host_info, net_sec, ssh, imagesize])

    @tornado.gen.coroutine
    def get_token(self, field_values):
        host, username, password, tenant = (field_values['hostname'],
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
    def get_networks(self, token_data):
        url = token_data[1]['network']

        req = HTTPRequest('%s/v2.0/networks' % url, 'GET', headers={
            'X-Auth-Token': token_data[0],
            'Accept': 'application/json'
        })
        try:
            resp = yield self.client.fetch(req)
        except:
            import traceback; traceback.print_exc()
            raise tornado.gen.Return([])
        body = json.loads(resp.body)
        networks = ['%s | %s' % (x['name'], x['id']) for x in body['networks']]
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_securitygroups(self, token_data, tenant):
        url = token_data[1]['compute']
        req = HTTPRequest('%s/os-security-groups' % (url), 'GET', headers={
            'X-Auth-Token': token_data[0],
            'Accept': 'application/json'
        })
        try:
            resp = yield self.client.fetch(req)
        except:
            import traceback; traceback.print_exc()
            raise tornado.gen.Return([])
        body = json.loads(resp.body)
        secgroups = body['security_groups']
        secgroups = ['%s | %s' % (x['name'], x['id']) for x in secgroups]
        raise tornado.gen.Return(secgroups)

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices={}
            ))
        elif step_index == 0:
            networks = []
            token_data = yield self.get_token(field_values)
            networks = yield self.get_networks(token_data)
            sec_groups = yield self.get_securitygroups(token_data, field_values['tenant'])
            services_plain = ['- %s:%s' % (x[0], x[1]) for x in token_data[1].iteritems()]
            services_plain = '; '.join(services_plain)
            desc = 'Token: %s Services: %s' % (token_data[0], services_plain)
            raise tornado.gen.Return(StepResult(errors=[], new_step_index=1,
                option_choices={
                    'network': networks,
                    'sec_group': sec_groups,
                    'netsec_desc': desc
                }
            ))
        elif step_index == 1:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=2, option_choices={
                    'ssh_desc': 'sdfaj*75%$$$xlLueHx'
                }
            ))
        elif step_index == 2:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=3, option_choices={
                    'image': ['img-1', 'img-2'],
                    'size': ['va-small', 'va-med']
                }
            ))
