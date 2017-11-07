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
from paramiko import SSHClient, AutoAddPolicy

PROVIDER_TEMPLATE = ""
PROFILE_TEMPLATE = ""

class GenericDriver(base.DriverBase):
    def __init__(self, provider_name = 'generic_provider', profile_name = 'generic_profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore = None, driver_name = 'generic_driver'):
        kwargs = {
            'driver_name' : driver_name, 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip,
            'key_name' : key_name, 
            'key_path' : key_path, 
            'datastore' : datastore
            }
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
        provider_datastore = yield self.datastore.get(provider['provider_name'])
        servers = provider_datastore.get('servers')

        servers = [x for x in servers if x['hostname'] != server_name]
        provider_datastore['servers'] = servers
        yield self.datastore.insert(provider['provider_name'], provider_datastore)

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
        servers = yield self.datastore.get(provider['provider_name'])
        servers = servers['servers']

        if provider['provider_name'] == 'va_standalone_servers' : 
            provider['provider_name'] = ''

        for i in servers: 
            i['provider'] = provider['provider_name']
        raise tornado.gen.Return(servers)
        


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
            'total_disk_usage_gb' : 0, 
            'current_disk_usage_mb' : 0, 
            'cpus_usage' :0, 
        }

#        servers = [
#            {
#                'providername' : 'name', 
#                'ipv4' : 'ipv4', 
#                'local_gb' : 0, 
#                'memory_mb' : 0, 
#                'status' : 'n/a', 
#            } for x in data['servers']
#        ]

        servers = yield self.get_servers(provider)

        provider_data = {
            'servers' : servers, 
            'limits' : {},
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
            })


            self.datastore.insert(field_values['provider_name'], {'servers' : []})
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
        #TODO Connect to ssh://data.get('ip') -p data.get('port')[ -u data.get('user') -pass data.get('pass') || -key data.get('key')
        print ('In create server. ')
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


        print ('Attempting connect with : ', connect_kwargs)
#        cl.connect(data.get('ip'), **connect_kwargs)

        # distro = ssh_session.cmd(['get', 'distro', 'cmd'])
        # instal = ssh_session.cmd(['install', 'salt', 'stuff'])
        # services are added on the api side. 
        provider_datastore = yield self.datastore.get(provider['provider_name'])
        servers = provider_datastore.get('servers')
        server = {"hostname" : data["server_name"], "ip" : data.get("ip"), "local_gb" : 0, "memory_mb" : 0, "status" : "n/a" }
        servers.append(server)

        provider_datastore['servers'] = servers
        yield self.datastore.insert(provider['provider_name'], provider_datastore)

        raise tornado.gen.Return(True)  
#        try:
#            yield super(GenericDriver, self).create_minion(provider, data)
#        except: 
#            import traceback

