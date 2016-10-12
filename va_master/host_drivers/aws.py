from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json

PROVIDER_TEMPLATE = '''VAR_PROVIDER_NAME:
  id: VAR_APP_ID
  key: VAR_APP_KEY
  keyname: VAR_KEYNAME
  private_key: VAR_PRIVATE_KEY
  driver: ec2

  minion:
    master: VAR_THIS_IP
    master_type: str

  grains: 
    node_type: broker
    release: 1.0.1

  # The name of the configuration profile to use on said minion
  #ubuntu if deploying on ubuntu
  ssh_username: ec2-user
  ssh_interface: private_ips

#  These are optional
#  location: VAR_LOCATION
#  availability_zone: VAR_AVAILABILITY_ZONE
'''


PROFILE_TEMPLATE = '''VAR_PROFILE_NAME:
    provider: VAR_PROVIDER_NAME
    image: VAR_IMAGE
    size: VAR_SIZE
    securitygroup: VAR_SEC_GROUP'''

class AWSDriver(base.DriverBase):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.profile_vars = {}
        self.provider_vars = {}
        self.profile = PROFILE_TEMPLATE
        self.provider = PROVIDER_TEMPLATE

    @tornado.gen.coroutine
    def driver_id(self):
        raise tornado.gen.Return('aws')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('AWS')

    @tornado.gen.coroutine
    def new_host_step_descriptions(self):
        raise tornado.gen.Return([
            {'name': 'Host Info'},
            {'name': 'Security'}
        ])

    @tornado.gen.coroutine
    def get_salt_configs(self, field_values, provider_name, profile_name):
        self.provider_vars['VAR_PROVIDER_NAME'] = provider_name
        self.provider_vars['VAR_KEYNAME'] = 'some_generated_keyname'
        self.provider_vars['VAR_PRIVATE_KEY'] = '/path/to/some/key'
        self.provider_vars['VAR_THIS_IP'] = '192.168.80.39' #Should get from the cli command

        self.profile_vars['VAR_PROFILE_NAME'] = profile_name
        self.profile_vars['VAR_PROVIDER_NAME'] = provider_name


        for var_name in self.profile_vars: 
            self.profile = self.profile.replace(var_name, self.profile_vars[var_name])
        for var_name in self.provider_vars: 
            self.provider = self.provider.replace(var_name, self.provider_vars[var_name])

        with open('/tmp/provider', 'w') as f: 
            f.write(self.provider)
        with open('/tmp/profile', 'w') as f: 
            f.write(self.profile)

        raise tornado.gen.Return((self.provider, self.profile))

    @tornado.gen.coroutine
    def get_steps(self):
        host_info = Step('Host info')
        host_info.add_str_field('app_id', 'Application ID')
        host_info.add_str_field('app_key', 'Application Key')

        net_sec = Step('Network & security group')
        net_sec.add_description_field('netsec_desc', 'Current connection info')
#        net_sec.add_options_field('network', 'Pick network')
        net_sec.add_options_field('sec_group', 'Pick security group')

        imagesize = Step('Image & size')
        imagesize.add_options_field('image', 'Image')
        imagesize.add_options_field('size', 'Size')

        raise tornado.gen.Return([host_info, net_sec, imagesize])

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices={}
            ))
        elif step_index == 0:
            self.provider_vars['VAR_APP_ID'] = field_values['app_id']
            self.provider_vars['VAR_APP_KEY'] = field_values['app_key']

            security_groups = ['list', 'of', 'security', 'groups']

            raise tornado.gen.Return(StepResult(errors=[], new_step_index=1, option_choices={                    'sec_group' : security_groups
            }))
        elif step_index == 1:
            self.profile_vars['VAR_SEC_GROUP'] = field_values['sec_group']
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=2, option_choices={
                    'image': ['img-1', 'img-2'],
                    'size': ['va-small', 'va-med']
                }
            ))
        else: 
            self.profile_vars['VAR_IMAGE'] = field_values['image']
            self.profile_vars['VAR_SIZE'] = field_values['size']

            configs = yield self.get_salt_configs([], 'provider', 'profile')
            raise tornado.gen.Return(configs)
#            yield hosts.create_host(some_args)

