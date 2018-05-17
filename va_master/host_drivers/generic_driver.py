try: 
    from . import base
    from .base import Step, StepResult
except: 
    import base
    from base import Step, StepResult

from va_master.api import apps
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json
import subprocess
import os
from paramiko import SSHClient, AutoAddPolicy

PROVIDER_TEMPLATE = ""
PROFILE_TEMPLATE = ""

class GenericDriver(base.DriverBase):
    def __init__(self, provider_name = 'generic_provider', profile_name = 'generic_profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore_handler = None, driver_name = 'generic_driver', flavours = []):
        kwargs = {
            'driver_name' : driver_name, 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip,
            'key_name' : key_name, 
            'key_path' : key_path, 
            'datastore_handler' : datastore_handler
            }
        self.sizes = flavours
        super(GenericDriver, self).__init__(**kwargs) 

    @tornado.gen.coroutine
    def driver_id(self):
        """ Pretty simple. """
        raise tornado.gen.Return('generic_driver')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('Generic provider')

      
    @tornado.gen.coroutine
    def get_provider_status(self, provider = ''): 
        raise tornado.gen.Return({'success' : True, 'message': ''})

    @tornado.gen.coroutine
    def get_steps(self):
        steps = yield super(GenericDriver, self).get_steps()
        steps[0].add_fields([('ip_address', 'IP address', 'str')])
        steps = [steps[0]]
        self.steps = steps
        raise tornado.gen.Return(steps)


    @tornado.gen.coroutine
    def get_networks(self):
        networks = [] 
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        
       	sec_groups =[] 
    	raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        
        images = []
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        
        sizes = []
        raise tornado.gen.Return(sizes)

    @tornado.gen.coroutine
    def remove_server(self, provider, server_name):
        provider_datastore = yield self.datastore_handler.get_provider(provider['provider_name'])
        servers = provider_datastore.get('servers')

        servers = [x for x in servers if x['hostname'] != server_name]
        provider_datastore['servers'] = servers
        yield self.datastore_handler.edit_provider(provider_datastore)

    @tornado.gen.coroutine
    def server_action(self, provider, server_name, action):
        
        server_action = {
            'delete' : self.remove_server, 
            'reboot' : 'reboot_function', 
            'start' : 'start_function', 
            'stop' : 'stop_function', 
        }
        if action not in server_action: 
            raise tornado.gen.Return({'success' : False, 'message' : 'Action not supported : ' +  action})

        success = yield server_action[action](provider, server_name)
        raise tornado.gen.Return({'success' : True, 'message' : ''})


    @tornado.gen.coroutine
    def get_servers(self, provider):
        servers = yield self.datastore_handler.get_provider(provider['provider_name'])
        servers = servers['servers']
        servers = [
            {
                'hostname' : x['hostname'], 
                'ip' : x['ip_address'],
                'size' : 'n/a',
                'used_disk' : 'n/a', 
                'used_ram' : 'n/a', 
                'used_cpu' : 'n/a',
                'status' : 'n/a', 
                'cost' : 0,  #TODO find way to calculate costs
                'estimated_cost' : 0,
                'managed_by' : x.get('managed_by', []), 
                'provider' : provider['provider_name'], 
            } for x in servers
        ]

        if provider['provider_name'] == 'va_standalone_servers' : 
            provider['provider_name'] = ''

        for i in servers: 
            i['provider'] = provider['provider_name']
        raise tornado.gen.Return(servers)
        

    @tornado.gen.coroutine
    def get_provider_billing(self, provider):
        raise tornado.gen.Return(None)


    @tornado.gen.coroutine
    def get_provider_data(self, provider, get_servers = True, get_billing = True):
        
        try: 
            data = {
                'servers' : [], 
                'limits' : {
                    'absolute' : [
                    ]
                }
            }
            #Functions that connect to provider here. 
        except Exception as e: 
            provider_data = {
                'servers' : [], 
                'limits' : {},
                'provider_usage' : {},
                'status' : {'success' : False, 'message' : 'Could not connect to the libvirt provider. ' + e}
            }
            raise tornado.gen.Return(provider_data)
           
        provider_usage = {
            'total_disk_usage_gb' : None, 
            'current_disk_usage_mb' : None, 
            'cpus_usage' :None, 
        }

        servers = yield self.get_servers(provider)

        provider_usage = {
            'max_cpus' : None,
            'used_cpus' : None, # TODO calculate cpus from servers
            'free_cpus' : None,
            'max_ram' : None,
            'used_ram' : None, # TODO calculate ram from servers
            'free_ram' : None,
            'max_disk' : None,
            'used_disk' : None, # TODO calculate disk from servers
            'free_disk' : None,
            'max_servers' : None,
            'used_servers' : len(servers),
            'free_servers' : None
        }

        provider_data = {
            'servers' : servers,
            'provider_usage' : provider_usage,
            'status' : {'success' : True, 'message': ''}
        }

        raise tornado.gen.Return(provider_data)



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        step_result = yield super(GenericDriver, self).validate_field_values(step_index, field_values)

        if step_index == 0: 
            self.field_values.update({
                'provider_name' : field_values['provider_name'], 
                'username' : field_values['username'], 
                'password' : field_values['password'],
                'ip_address' : field_values['ip_address'],
                'images' : [], 
                'sizes' : self.sizes, 
            })
            raise tornado.gen.Return(StepResult(
                errors = [], new_step_index = -1, option_choices = {}
            ))
        raise tornado.gen.Return(step_result)
       
     
    @tornado.gen.coroutine
    def validate_app_fields(self, step, **fields):
        steps_fields = [['role', 'server_name'], [], ['username', 'ip', 'port', 'location']]
        result = yield super(GenericDriver, self).validate_app_fields(step, steps_fields = steps_fields, **fields)
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def create_server(self, provider, data):
        cl = SSHClient()
        cl.load_system_host_keys()
        cl.set_missing_host_key_policy(AutoAddPolicy())
        connect_kwargs = {
            'username' : data.get('username', ''), 
        }
        if data.get('port'): 
            connect_kwargs['port'] = int(data.get('port'))

        if data.get('password'): 
            connect_kwargs['password'] = data['password']
        else: 
            connect_kwargs['key_filename'] = self.key_path + '.pem'


        try:
            cl.connect(data.get('ip'), **connect_kwargs)
        except Exception as e: 
            print ('Failed to connect with ssh to ', data.get('ip'))
            import traceback
            traceback.print_exc()
            raise Exception('Failed to connect with ssh: ' + e.message)

        server = {"server_name" : data["server_name"], "hostname" : data["server_name"], "ip_address" : data["ip"], "local_gb" : 0, "memory_mb" : 0, "status" : "n/a" , "managed_by" : ['ssh'], "location" : data.get('location', '')}

        yield apps.add_server_to_datastore(self.datastore_handler, server_name = server['server_name'], ip_address = data['ip'], hostname = server['hostname'], manage_type = 'ssh', username = data.get('username', ''), driver_name = 'generic_driver', kwargs = {'password' : data.get('password', ''), 'location' : data.get('location', '')})
        db_server = yield self.datastore_handler.get_object('server', server_name = server['server_name'])

        if provider['provider_name'] != 'va_standalone_servers' : 
            yield apps.manage_server_type(self.datastore_handler, server_name = server['server_name'], new_type = 'provider', driver_name = 'generic_driver')
            server['managed_by'].append('provider')

        yield self.datastore_handler.add_generic_server(provider, server)

        raise tornado.gen.Return(True)  

