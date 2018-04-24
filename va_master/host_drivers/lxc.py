try: 
    from . import base
    from .base import Step, StepResult
except: 
    import base
    from base import Step, StepResult

from base import bytes_to_int, int_to_bytes

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json, datetime, subprocess, os

from pylxd import Client

#TODO need to see how to actually write the provider conf
PROVIDER_TEMPLATE = '''VAR_PROVIDER_NAME:
  minion:
    master: VAR_THIS_IP
    master_type: str
  # The name of the configuration profile to use on said minion
  driver: lxc 
  ssh_key_names: VAR_KEYPAIR_NAME
  ssh_key_file: VAR_SSH_FILE
  ssh_interface: private_ips
  location: VAR_LOCATION
  backups_enabled: True
  ipv6: True
  create_dns_record: True
'''


PROFILE_TEMPLATE = '''VAR_PROFILE_NAME:
    provider: VAR_PROVIDER_NAME
    template: VAR_TEMPLATE
    backing: lvm
    vgname: vg1
    lvname: lxclv
    size: VAR_SIZE

    minion:
        master: VAR_THIS_IP
        grains:
            role: VAR_ROLE
    networks:
      - fixed:
          - VAR_NETWORK_ID 
'''

class LXCDriver(base.DriverBase):
    def __init__(self, flavours, provider_name = 'digital_ocean_provider', profile_name = 'digital_ocean_profile', host_ip = '', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore_handler = None):
        """ The standard issue init method. Borrows most of the functionality from the BaseDriver init method, but adds a self.regions attribute, specific for OpenStack hosts. """

        kwargs = {
            'driver_name' : 'digital_ocean',
            'provider_template' : PROVIDER_TEMPLATE,
            'profile_template' : PROFILE_TEMPLATE,
            'provider_name' : provider_name,
            'profile_name' : profile_name,
            'host_ip' : host_ip,
            'key_name' : key_name,
            'key_path' : key_path, 
            'datastore_handler' : datastore_handler
            }

        self.flavours = flavours
        super(LXCDriver, self).__init__(**kwargs)

    def get_client(self, provider):
        self.cl = Client(provider['provider_ip'], verify = False)
        self.cl.authenticate(provider['password'])
        return self.cl

    def get_server_addresses(self, s):
        if not s['state'].get('network'): 
            return ['']
        return [i.get('address') for i in s['state'].get('network', {}).get('eth0', {}).get('addresses', [{}]) if i.get('family', '') == 'inet'] or ['']


    def get_server_usage(self, server, key):
        if not server['state'].get(key):
            return 0 
        return server['state'][key].get('usage', 0)


    @tornado.gen.coroutine
    def driver_id(self):
        """ Pretty simple. """
        raise tornado.gen.Return('lxc')

    @tornado.gen.coroutine
    def friendly_name(self):
        """ Pretty simple """
        raise tornado.gen.Return('LXC')

    @tornado.gen.coroutine
    def get_steps(self):
        """ Digital Ocean requires an access token in order to generate the provider conf.  """

        steps = yield super(LXCDriver, self).get_steps()
        steps[0].add_fields([
            ('provider_ip', 'IP of the lxc host.', 'str'),
        ])
        self.steps = steps
        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_networks(self):
        """ Gets the networks the salt-cloud method, at least for the moment. """
        networks = [x.name for x in self.cl.networks.all()]
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        """ No security groups for digital ocean.  """
        sec_groups = ['No security groups. ']
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        """ Gets the images using salt-cloud. """
        images = [x.properties['description'] for x in self.cl.images.all()]
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        """ Gets the sizes using salt-cloud.  """
        sizes = self.flavours.keys()
        raise tornado.gen.Return(sizes)


    @tornado.gen.coroutine
    def get_servers(self, provider):
        cl = self.get_client(provider)
        servers = cl.containers.all()
        servers = [{'server' : x, 'state' : x.state().__dict__} for x in servers]


        servers = [
            {
                'hostname' : x['server'].name,
                'ip' : self.get_server_addresses(x)[0],
                'size' : x['server'].name,
                'used_disk' : self.get_server_usage(x, 'disk') / float(2**20),
                'used_ram' : self.get_server_usage(x, 'memory') / float(2**20),
                'used_cpu' : self.get_server_usage(x, 'cpu'), #TODO calculate CPU usage - current value is CPU time in seconds, we need to find total uptime and divide by it. 
                'status' : x['server'].status, 
                'cost' : 0,  #TODO find way to calculate costs
                'estimated_cost' : 0,
                'provider' : provider['provider_name'], 
            } for x in servers
        ]
        raise tornado.gen.Return(servers)



    @tornado.gen.coroutine
    def get_provider_status(self, provider):
        """ TODO """
        try:
            cl = self.get_client(provider)
            raise tornado.gen.Return({'success' : True, 'message' : ''})
        except Exception as e: 
            raise tornado.gen.Return({'success' : False, 'message' : e.message})


    @tornado.gen.coroutine
    def get_provider_billing(self, provider):
        #TODO provide should have some sort of costing mechanism, and we multiply used stuff by some price. 

        total_cost = 0
        servers = yield self.get_servers(provider)

        servers.append({
            'hostname' : 'Other Costs',
            'ip' : '',
            'size' : '',
            'used_disk' : 0,
            'used_ram' : 0,
            'used_cpu' : 0,
            'status' : '',
            'cost' : total_cost,
            'estimated_cost' : 0, 
            'provider' : provider['provider_name'],
        })

        total_memory = sum([x['used_ram'] for x in servers if not type('used_ram') == str])
        total_memory = int_to_bytes(total_memory)
        provider['memory'] = total_memory


        for server in servers: 
            server['used_ram'] = int_to_bytes(server['used_ram'] * (2 ** 20))

        billing_data = {
            'provider' : provider, 
            'servers' : servers,
            'total_cost' : total_cost
        }
        raise tornado.gen.Return(billing_data)




    @tornado.gen.coroutine
    def get_provider_data(self, provider, get_servers = True, get_billing = True):
        """ TODO """

        servers = yield self.get_servers(provider)

        get_sum = lambda x: sum([s[x] for s in servers if not type(s[x]) == str])

        provider_usage = {
            'max_cpus' : 'n/a',
            'used_cpus' : get_sum('used_cpu'), 
            'free_cpus' : 'n/a', 
            'max_ram' : 'n/a', 
            'used_ram' : get_sum('used_ram'),
            'free_ram' : 'n/a', 
            'max_disk' : 'n/a', 
            'used_disk' : get_sum('used_disk'), 
            'free_disk' : 'n/a',
            'max_servers' : 'n/a', 
            'used_servers' : len(servers), 
            'free_servers' : 'n/a'
        }

        provider_data = {
            'servers' : servers, 
            'provider_usage' : provider_usage,
            'status' : {'success' : True, 'message': ''}
        }
        raise tornado.gen.Return(provider_data)


    @tornado.gen.coroutine
    def get_driver_trigger_functions(self):
        conditions = []
        actions = []
        return {'conditions' : conditions, 'actions' : actions}


    @tornado.gen.coroutine
    def server_action(self, provider, server_name, action):
        """ Performs server actions using a nova client. """
        message = ''
        try:
            cl = self.get_client(provider)

            server = cl.containers.get(server_name)
            getattr(server, action)()
        except Exception as e:
            import traceback
            traceback.print_exc()

            raise Exception('Could not get server' + server_name + '. ' + e.message)
        try:
            pass
            #TODO perform action
        except Exception as e:
            import traceback
            traceback.print_exc()

            raise Exception('Action ' + action + ' was not performed on ' + server_name + '. Reason: ' + e.message)

        raise tornado.gen.Return({'success' : True, 'message' : message, 'data' : {}})



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        """ Uses the base driver method, but adds the region tenant and identity_url variables, used in the configurations. """
        if step_index == 0:
            self.field_values['provider_ip'] = field_values['provider_ip']
            cl = self.get_client(field_values)
        try:
            step_result = yield super(LXCDriver, self).validate_field_values(step_index, field_values)
        except:
            import traceback
            traceback.print_exc()
        raise tornado.gen.Return(step_result)


    @tornado.gen.coroutine
    def create_server(self, provider, data):
        try:
            lxc_config = {'name' : data['server_name'], 'source' : {'image' : data['image'], 'network' : data['network'], 'size' : data['size']}}
            cl = self.get_client(provider)

            #NOTE this is almost definitely not the right way to do this. We should be using aliases or something. 
            image = [x for x in cl.images.all() if x.properties.get('description', '') == data['image']]
            #NOTE temporary until we figure out how to look up images
            image = cl.images.all()[0]

            network = cl.networks.get(data['network'])

            lxc_config = {
                'name' : data['server_name'], 
                'source' : {
                    'type' : 'image', 
                    'properties' : {
                        'os' : image.properties['os'], 
                        'architecture' : image.properties['architecture'], 
                        'release' : image.properties['release'], 
                        'description' : image.properties.get('description', '')
                    }
                }
            }

            print ('My conf is : ', lxc_config)
#            lxc_config = {'name' : data['server_name'], 'source' : {'type' : 'image', 'alias' : 'ubuntu/16.04'}}

            new_container = cl.containers.create(lxc_config, wait = True)
            raise tornado.gen.Return(new_container)
        except:
            import traceback
            traceback.print_exc()

