try: 
    from . import base
    from .base import Step, StepResult
except: 
    import base
    from base import Step, StepResult

from base import bytes_to_int, int_to_bytes

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import digitalocean
from digitalocean import Manager
import tornado.gen
import json, datetime, subprocess, os

PROVIDER_TEMPLATE = '''VAR_PROVIDER_NAME:
  minion:
    master: VAR_THIS_IP
    master_type: str
  # The name of the configuration profile to use on said minion

  driver: digitalocean 
  personal_access_token: VAR_TOKEN
  ssh_key_names: VAR_SSH_NAME
  ssh_key_file: VAR_SSH_FILE
  ssh_interface: private
  private_networking: True
  location: VAR_LOCATION
  backups_enabled: True
  ipv6: True
'''

#    userdata_file: VAR_USERDATA_FILE

PROFILE_TEMPLATE = '''VAR_PROFILE_NAME:
    provider: VAR_PROVIDER_NAME
    image: VAR_IMAGE
    size: VAR_SIZE

    minion:
        master: VAR_THIS_IP
        grains:
            role: VAR_ROLE
'''

class DigitalOceanDriver(base.DriverBase):
    def __init__(self, provider_name = 'digital_ocean_provider', profile_name = 'digital_ocean_profile', host_ip = '', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore_handler = None):
        """ The standard issue init method. Borrows most of the functionality from the BaseDriver init method. """

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
        #TODO get from api
        #[x.name for x in m.get_all_regions()]
        self.locations = [u'New York 1', u'Singapore 1', u'London 1', u'New York 3', u'Amsterdam 3', u'Frankfurt 1', u'Toronto 1', u'San Francisco 2', u'Bangalore 1']

        super(DigitalOceanDriver, self).__init__(**kwargs)

    def get_manager(self, provider):

        manager = Manager(token=provider['token'])
        self.manager = manager
        return manager

    @tornado.gen.coroutine
    def driver_id(self):
        """ Pretty simple. """
        raise tornado.gen.Return('digital_ocean')

    @tornado.gen.coroutine
    def friendly_name(self):
        """ Pretty simple """
        raise tornado.gen.Return('Digital Ocean')

    @tornado.gen.coroutine
    def get_steps(self):
        """ Digital Ocean requires an access token in order to generate the provider conf.  """

        steps = yield super(DigitalOceanDriver, self).get_steps()
        steps[0].remove_fields(['username', 'password', 'location'])
        steps[0].add_fields([
            ('token', 'Access token', 'str'),
            ('location', 'Location', 'options'),
        ])

        steps.pop(1)
        self.steps = steps
        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_networks(self):
        """ Gets the networks the salt-cloud method, at least for the moment. """
        networks = yield super(DigitalOceanDriver, self).get_networks()
        networks = ['Digital ocean has no networks. ']
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        """ No security groups for digital ocean.  """
        sec_groups = ['DigitalOcean has no security groups. ']
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        """ Gets the images using salt-cloud. """
        images = [x.name for x in self.manager.get_images()]
        print ('Images are : ', images)
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        """ Gets the sizes using salt-cloud.  """
        sizes = [x.slug for x in self.manager.get_all_sizes()]
        print ('Sizes are : ', sizes)
        raise tornado.gen.Return(sizes)


    @tornado.gen.coroutine
    def get_servers(self, provider):
        """ TODO  """

        manager = self.get_manager(provider)
        servers = manager.get_all_droplets()
        servers = [
            {
                'hostname' : x.name, 
                'ip' : x.ip_address,
                'size' : x.size['slug'],
                'used_disk' : str(x.size['disk']) + 'GB', 
                'used_ram' : x.memory, 
                'used_cpu' : x.vcpus,
                'status' : x.status, 
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
            self.get_manager(provider)
        except Exception as e: 
            raise tornado.gen.Return({'success' : False, 'message' : e.message})
        raise tornado.gen.Return({'success' : True, 'message' : ''})


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

        total_memory = sum([x['used_ram'] for x in servers]) * 2**20
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

        provider_usage = {
            'max_cpus' : 'maxTotalCores',
            'used_cpus' : 'totalCoresUsed', 
            'free_cpus' : 'maxTotalCores', 
            'max_ram' : 'maxTotalRAMSize', 
            'used_ram' : 'totalRAMUsed',
            'free_ram' : 'maxTotalRAMSize', 
            'max_disk' : 'maxTotalVolumeGigabytes', 
            'used_disk' : 'totalGigabytesUsed', 
            'free_disk' : 'maxTotalVolumeGigabytes',
            'max_servers' : 'maxTotalInstances', 
            'used_servers' : 'totalInstancesUsed', 
            'free_servers' : 'maxTotalInstances'
        }

        provider_data = {
            'servers' : servers, 
            'provider_usage' : provider_usage,
            'status' : {'success' : True, 'message': ''}
        }
        raise tornado.gen.Return(provider_data)


    @tornado.gen.coroutine
    def get_driver_trigger_functions(self):
        conditions = ['domain_full', 'server_can_add_memory', 'server_can_add_cpu']
        actions = ['server_new_terminal', 'server_cpu_full', 'server_memory_full', 'server_set_status', 'server_cpu_critical', 'server_cpu_warning', 'server_cpu_ok', 'server_memory_ok', 'server_memory_warning', 'server_memory_critical', 'server_cpu_full_ok', 'server_memory_full_ok']
        return {'conditions' : conditions, 'actions' : actions}


    @tornado.gen.coroutine
    def server_action(self, provider, server_name, action):
        """ Performs server actions using a nova client. """
        try:
            message = 'Success!'
            manager = self.get_manager(provider)
            servers = manager.get_all_droplets()
            server = [x for x in servers if x.name == server_name][0]
        except Exception as e:
            import traceback
            traceback.print_exc()

            raise Exception('Could not get server' + server_name + '. ' + e.message)
        try:
            server_action = {
                'delete' : server.destroy,
                'reboot' : server.power_off,
                'start' : server.power_on,
                'stop' : server.shutdown, 
#                'suspend' : server.suspend,
#                'resume' : server.resume,
            }
            server_action[action]()
        except Exception as e:
            import traceback
            traceback.print_exc()

            raise Exception('Action ' + action + ' was not performed on ' + server_name + '. Reason: ' + e.message)

        raise tornado.gen.Return({'success' : True, 'message' : message, 'data' : {}})



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        """ Uses the base driver method, but adds the region tenant and identity_url variables, used in the configurations. """

        options = {}

        if step_index == -1: 
            options = {'location' : self.locations}
        
        if step_index == 0:
            self.token = field_values['token']
            self.get_manager({'token' : self.token})
            self.provider_vars['VAR_TOKEN'] = field_values['token']

            images = yield self.get_images()
            sizes =yield self.get_sizes()              

            self.field_values['images'] = images
            self.field_values['sizes'] = sizes
            options = {'image' : images, 'size' : sizes}

        if step_index > 0: 
            step_index += 1
        try:
            print ('Validating step ', step_index)
            step_result = yield super(DigitalOceanDriver, self).validate_field_values(step_index, field_values, options = options)
        except:
            import traceback
            traceback.print_exc()
        raise tornado.gen.Return(step_result)


    @tornado.gen.coroutine
    def create_server(self, host, data):
        """ Works properly with the base driver method, but overwritten for bug tracking. """
        try:
            yield super(DigitalOceanDriver, self).create_minion(host, data)

            #Once a server is created, we revert the templates to the originals for creating future servers. 
            self.profile_template = PROFILE_TEMPLATE
            self.provider_template = PROVIDER_TEMPLATE
        except:
            import traceback
            traceback.print_exc()

