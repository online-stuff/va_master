from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json
import subprocess

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
    def __init__(self, provider_name = 'openstack_provider', profile_name = 'openstack_profile', host_ip = '192.168.80.39', key_name = '', key_path = '/root/openstack_key'):

        if not key_name: 
            #probably use uuid instead
            key_name = 'openstack_key_name'

        self.key_path = key_path + ('/' * (not key_path[-1] == '/')) + key_name
        self.key_name = key_name

        print 'Path is : ', self.key_path, ' key name is : ', self.key_name

        provider_vars = {'VAR_THIS_IP' : host_ip, 'VAR_PROVIDER_NAME' : provider_name, 'VAR_SSH_NAME' : key_name, 'VAR_SSH_FILE' : self.key_path + '.pem'}
        profile_vars = {'VAR_PROVIDER_NAME' : provider_name, 'VAR_PROFILE_NAME' : profile_name}
        self.regions = ['RegionOne', ]
        super(OpenStackDriver, self).__init__(PROVIDER_TEMPLATE, PROFILE_TEMPLATE, provider_vars = provider_vars, profile_vars = profile_vars)


    def cmd_with_environ_vars(self, cmd):
        cmd = ['OS_USERNAME=' + self.provider_vars['VAR_USERNAME'],
                'OS_PROJECT_NAME=' + self.provider_vars['VAR_TENANT'], 
                'OS_AUTH_URL=%s' % (self.provider_vars['VAR_IDENTITY_URL'].split('/tokens')[0]), 
                'OS_PASSWORD=' + self.provider_vars['VAR_PASSWORD']] + cmd 
        return cmd


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
    def get_salt_configs(self):
        yield super(OpenStackDriver, self).get_salt_configs()
        
        with open('/etc/salt/cloud.providers.d/test_openstack_provider.conf', 'w') as f: 
            f.write(self.provider_template)
        with open('/etc/salt/cloud.profiles.d/test_openstack_profile.conf', 'w') as f: 
            f.write(self.profile_template)
        #tornado.gen.Return (self.provider_template, self.profile_template)

    @tornado.gen.coroutine
    def get_steps(self):
        host_info = Step('Host info')
        host_info.add_field('hostname', 'Keystone hostname:port (xx.xx.xxx.xx:35357)', type = 'str')
        host_info.add_field('username', 'Username', type = 'str')
        host_info.add_field('password', 'Password', type = 'str')
        host_info.add_field('tenant', 'Tenant', type = 'str')
        host_info.add_field('region', 'Region', type = 'options')


        net_sec = Step('Network & security group')
        net_sec.add_description_field('netsec_desc', 'Current connection info')
        net_sec.add_field('network', 'Pick network', type = 'options')
        net_sec.add_field('sec_group', 'Pick security group', type = 'options')

        ssh = Step('SSH key')
        ssh.add_description_field('ssh_desc', 'Import this keypair into Openstack')
        ssh.add_field('private_key_name', 'Name of key', type = 'str')

        imagesize = Step('Image & size')
        imagesize.add_field('image', 'Image', type = 'options')
        imagesize.add_field('size', 'Size', type = 'options')
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
                errors=[], new_step_index=0, option_choices={'region' : self.regions,}
            ))
        elif step_index == 0:
            self.provider_vars['VAR_USERNAME'] = field_values['username']
            self.provider_vars['VAR_TENANT'] = field_values['tenant']
            self.provider_vars['VAR_PASSWORD'] = field_values['password']
            self.provider_vars['VAR_IDENTITY_URL'] ='http://' + field_values['hostname'] + '/v2.0/tokens'
            self.provider_vars['VAR_REGION'] = field_values['region']


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
            self.provider_vars['VAR_NETWORK_ID'] = field_values['network']
            self.profile_vars['VAR_SEC_GROUP'] = field_values['sec_group']
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=2, option_choices={
                    'ssh_desc': 'sdfaj*75%$$$xlLueHx'
                }
            ))
        elif step_index == 2:
            cmd_images = ['nova', 'image-list']
            cmd_sizes = ['nova', 'flavor-list']

            images = subprocess.check_output(cmd_images)
            sizes = subprocess.check_output(cmd_sizes)

            images = [x.split('|')[2].strip() for x in images.split('\n')[3:-2]]            
            sizes = [x.split('|')[2].strip() for x in sizes.split('\n')[3:-2]]
 
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=3, option_choices={
                    'image': images,
                    'size': sizes,
                }
            ))
        else:
            self.profile_vars['VAR_IMAGE'] = field_values['image']
            self.profile_vars['VAR_SIZE'] = field_values['size']
            
            cmd_keypair = ['nova', 'keypair-add', self.key_name, '>', self.key_path + '.pem']
            with open('/tmp/keypair_test', 'w') as f: 
                f.write(subprocess.list2cmdline(cmd_keypair))

            subprocess.call(cmd_keypair)
            yield self.get_salt_configs()
