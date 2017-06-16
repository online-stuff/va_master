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
  minion:
    master: VAR_THIS_IP
    master_type: str
  # The name of the configuration profile to use on said minion
  driver: openstack
  auth_version: 2
  compute_name: nova
  protocol: ipv4
  ssh_key_name: VAR_SSH_NAME
  ssh_key_file: VAR_SSH_FILE
  ssh_interface: private_ips
  use_keystoneauth: True
  user: VAR_USERNAME
  tenant: VAR_TENANT
  password: VAR_PASSWORD
  identity_url: VAR_IDENTITY_URL
  compute_region: VAR_REGION
'''

PROFILE_TEMPLATE = '''VAR_PROFILE_NAME:
    provider: VAR_PROVIDER_NAME
    image: VAR_IMAGE
    size: VAR_SIZE
    securitygroups: VAR_SEC_GROUP
    ssh_username: VAR_IMAGE_USERNAME
    minion:
        grains:
            role: VAR_ROLE
    networks:
      - fixed:
          - VAR_NETWORK_ID 
'''

class OpenStackDriver(base.DriverBase):
    def __init__(self, provider_name = 'openstack_provider', profile_name = 'openstack_profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore = None):
        """ The standard issue init method. Borrows most of the functionality from the BaseDriver init method, but adds a self.regions attribute, specific for OpenStack hosts. """

        kwargs = {
            'driver_name' : 'openstack',
            'provider_template' : PROVIDER_TEMPLATE,
            'profile_template' : PROFILE_TEMPLATE,
            'provider_name' : provider_name,
            'profile_name' : profile_name,
            'host_ip' : host_ip,
            'key_name' : key_name,
            'key_path' : key_path, 
            'datastore' : datastore
            }
        self.regions = ['RegionOne', ]
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
    def export_env_variables(self, username, tenant, url, password):
        """ A method I made to help call nova commands, but not being used actively. Keeping it here in case it's needed some time. """

        os.environ['OS_USERNAME'] = self.provider_vars['VAR_USERNAME']
        os.environ['OS_PROJECT_NAME'] = self.provider_vars['VAR_TENANT']
        os.environ['OS_AUTH_URL'] = self.provider_vars['VAR_IDENTITY_URL']
        os.environ['PASSWORD'] = self.provider_vars['VAR_PASSWORD']

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
    def get_token(self, field_values):
        """ 
            Gets a token from an OpenStack server which is used to get OpenStack values 

            Arguments: 
            field_values -- A dictionary containing information about the host. It must have a host_ip, username, password and tenant value. The host_ip should be the base ip with the port, for instance 192.168.80.16:5000. 
        """

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
        """
            Gets a specified value by using the OpenStack REST api. 

            Arguments: 
            token_data -- The token data from which we can extract the URLs for various resources. This is the data received with the get_token() method. 
            token_value -- The resource that we need to take. Check the OpenStack REST API documentation for reference, or some of this driver's methods which use this (get_networks, get_images etc. )
            url_endpoint -- The specific values we want to get. It varies from resource to resource so again, check the OpenStack documentation, or the other methods. 
        """

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
        """ Gets the networks using the get_openstack_value() method. """
        try: 
            tenants = yield self.get_openstack_value(self.token_data, 'identity', 'projects')
            tenant = [x for x in tenants['projects'] if x['name'] == self.field_values['tenant']][0]

        except: 
            tenants = yield self.get_openstack_value(self.token_data, 'identity', 'tenants')
            tenant = [x for x in tenants['tenants'] if x['name'] == self.field_values['tenant']][0]
          

        tenant_id = tenant['id']

        networks = yield self.get_openstack_value(self.token_data, 'network', 'v2.0/networks?tenant_id=%s'%(tenant_id))
        networks = ['|'.join([x['name'], x['id']]) for x in networks['networks']]
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        """ Gets the security groups using the get_openstack_value() method. """
       	sec_groups = yield self.get_openstack_value(self.token_data, 'compute', 'os-security-groups')
        sec_groups = ['|'.join([x['name'], x['id']]) for x in sec_groups['security_groups']]
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        """ Gets the images using the get_openstack_value() method. """
        images = yield self.get_openstack_value(self.token_data, 'image', 'v2.0/images')
        images = [x['name'] for x in images['images']]
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        """ Gets the sizes using the get_openstack_value() method. """
        sizes = yield self.get_openstack_value(self.token_data, 'compute', 'flavors')
        sizes = [x['name'] for x in sizes['flavors']]
        raise tornado.gen.Return(sizes)


    @tornado.gen.coroutine
    def get_instances(self, host):
        """ Gets various information about the instances so it can be returned to host_data. The format of the data for each instance follows the same format as in the base driver description """
        try:
            self.token_data = yield self.get_token(host)

            flavors = yield self.get_openstack_value(self.token_data, 'compute', 'flavors/detail')
            flavors = flavors['flavors']

            servers = yield self.get_openstack_value(self.token_data, 'compute', 'servers/detail')
            servers = servers['servers']

            try: 
                tenants = yield self.get_openstack_value(self.token_data, 'identity', 'projects')
                tenant = [x for x in tenants['projects'] if x['name'] == host['tenant']][0]

            except: 
                tenants = yield self.get_openstack_value(self.token_data, 'identity', 'tenants')
                tenant = [x for x in tenants['tenants'] if x['name'] == host['tenant']][0]
             

            tenant_id = tenant['id']
            tenant_usage = yield self.get_openstack_value(self.token_data, 'compute', 'os-simple-tenant-usage/' + tenant_id)

            tenant_usage = tenant_usage['tenant_usage']
            instances = [
                {
                    'hostname' : x['name'], 
                    'ip' : x['addresses'].get('private_vapps', x['addresses'].get('public', [{'addr':'n/a'}]))[0]['addr'], #[x['addresses'].keys()[0]], 
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
    def get_host_data(self, host, get_instances = True, get_billing = True):
        """ Gets various data about the host and all the instances using the get_openstack_value() method. Returns the data in the same format as defined in the base driver. """
        try:
            self.token_data = yield self.get_token(host)

            try: 
                tenants = yield self.get_openstack_value(self.token_data, 'identity', 'projects')
                tenant = [x for x in tenants['projects'] if x['name'] == host['tenant']][0]
            except: 
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

        if get_instances: 
            instances = yield self.get_instances(host)
        else: 
            instances = []

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
            step_result = yield super(OpenStackDriver, self).validate_field_values(step_index, field_values)
        except:
            import traceback
            traceback.print_exc()
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
            yield super(OpenStackDriver, self).create_minion(host, data)
        except:
            import traceback
            traceback.print_exc()
