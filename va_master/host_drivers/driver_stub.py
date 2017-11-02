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

class {{ driver_name }}Driver(base.DriverBase):
    def __init__(self, provider_name = '_provider', profile_name = '_profile', host_ip = '192.168.80.39'):
        kwargs = {
            'driver_name' : 'driver', 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip
            }
        super({{ driver_name }}Driver, self).__init__(**kwargs) 

    @tornado.gen.coroutine
    def driver_id(self):
        raise tornado.gen.Return('{{ driver_id }}')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('{{ driver_friendly }}')


    @tornado.gen.coroutine
    def get_steps(self):
        steps = yield super({{driver_name}}Driver, self).get_steps()
        self.steps = steps
        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_networks(self):
        networks = ['list', 'of', 'networks']
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        sec_groups = ['list', 'of', 'security', 'groups']
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        images = ['list', 'of', 'images']
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        sizes = ['list', 'of', 'sizes']
        raise tornado.gen.Return(sizes)

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
    	    raise tornado.gen.Return(StepResult(
        		errors=[], new_step_index=0, option_choices={'region' : self.regions,}
    	    ))
        elif step_index == 0:
            self.field_values['networks'] = yield self.get_networks() 
            self.field_values['sec_groups'] = yield self.get_sec_groups()
            self.field_values['images'] = yield self.get_images()
            self.field_values['sizes']= yield self.get_sizes()


       	step_kwargs = yield super({{driver_name}}Driver, self).validate_field_values(step_index, field_values)
        raise tornado.gen.Return(StepResult(**step_kwargs))
       
