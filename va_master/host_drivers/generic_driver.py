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


PROVIDER_TEMPLATE = ""
PROFILE_TEMPLATE = ""

class GenericDriver(base.DriverBase):
    def __init__(self, provider_name = 'generic_provider', profile_name = 'generic_profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore = None):
        kwargs = {
            'driver_name' : 'generic_driver', 
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
        raise tornado.gen.Return('Generic host')

      
    @tornado.gen.coroutine
    def get_host_status(self, host = ''): 
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
    def instance_action(self, host, instance_name, action):
        
        instance_action = {
            'delete' : 'delete_function', 
            'reboot' : 'reboot_function', 
            'start' : 'start_function', 
            'stop' : 'stop_function', 
        }
        if action not in instance_action: 
            raise tornado.gen.Return({'success' : False, 'message' : 'Action not supported : ' +  action})

        success = instance_action[action](instance_name)
        raise tornado.gen.Return({'success' : True, 'message' : ''})


    @tornado.gen.coroutine
    def get_instances(self, host):
        instances = yield self.datastore.get(host['hostname'])
        instances = instances['instances']
        raise tornado.gen.Return(instances)
        


    @tornado.gen.coroutine
    def get_host_data(self, host, get_instances = True, get_billing = True):
        
        try: 
            data = {
                'instances' : [], 
                'limits' : {
                    'absolute' : [
                    ]
                }
            }
            #Functions that connect to host here. 
        except Exception as e: 
            host_data = {
                'instances' : [], 
                'limits' : {},
                'host_usage' : {},
                'status' : {'success' : False, 'message' : 'Could not connect to the libvirt host. ' + e}
            }
            raise tornado.gen.Return(host_data)
           
        host_usage = {
            'total_disk_usage_gb' : 0, 
            'current_disk_usage_mb' : 0, 
            'cpus_usage' :0, 
        }

#        instances = [
#            {
#                'hostname' : 'name', 
#                'ipv4' : 'ipv4', 
#                'local_gb' : 0, 
#                'memory_mb' : 0, 
#                'status' : 'n/a', 
#            } for x in data['instances']
#        ]

        instances = yield self.get_instances(host)

        host_data = {
            'instances' : instances, 
            'limits' : {},
            'host_usage' : host_usage, 
            'status' : {'success' : True, 'message': ''}
        }
        raise tornado.gen.Return(host_data)



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        step_result = yield super(GenericDriver, self).validate_field_values(step_index, field_values)
        if step_index == 0: 
            self.field_values.update({
                'hostname' : field_values['hostname'], 
                'username' : field_values['username'], 
                'password' : field_values['password'],
                'ip_address' : field_values['ip_address'],
            })


            self.datastore.insert(field_values['hostname'], {'instances' : []})
            raise tornado.gen.Return(StepResult(
                errors = [], new_step_index = -1, option_choices = {}
            ))
        raise tornado.gen.Return(step_result)
       
      
    @tornado.gen.coroutine
    def create_minion(self, host, data):
        raise tornado.gen.Return(True)  
        try:
            yield super(GenericDriver, self).create_minion(host, data)
        except: 
            import traceback
