from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json
import subprocess
import os

PROVIDER_TEMPLATE = '''VAR_PROVIDER_NAME:
  auth_minion: VAR_THIS_IP
  minion:
    master: VAR_THIS_IP
    master_type: str
  # The name of the configuration profile to use on said minion
  ssh_key_name: VAR_SSH_NAME
  ssh_key_file: VAR_SSH_FILE
  ssh_interface: private_ips
  driver: ###INSERT DRIVER HERE###
  ###INSERT OTHER VARIABLES HERE###
'''

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
    def __init__(self, provider_name = 'driver_provider', profile_name = 'driver_profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master_key'):
        kwargs = {
            'driver_name' : 'driver_name', 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip,
            'key_name' : key_name, 
            'key_path' : key_path
            }
        super(Driver, self).__init__(**kwargs) 

    @tornado.gen.coroutine
    def driver_id(self):
        raise tornado.gen.Return('driver_id')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('Driver name')

      
    @tornado.gen.coroutine
    def get_steps(self):
        steps = yield super(Driver, self).get_steps()
        self.steps = steps
        raise tornado.gen.Return(steps)





    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        if step_index == 0:
    	    self.field_values['networks'] = yield self.get_networks() 
            self.field_values['sec_groups'] = yield self.get_sec_groups()
            self.field_values['images'] = yield self.get_images()
            self.field_values['sizes']= yield self.get_sizes()
        step_kwargs = yield super(Driver, self).validate_field_values(step_index, field_values)
        raise tornado.gen.Return(StepResult(**step_kwargs))
       
      
    @tornado.gen.coroutine
    def create_minion(self, host, data):
        try:
            yield super(Driver, self).create_minion(host, data)
        except: 
            import traceback
            traceback.print_exc()
