from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json
from va_master import datastore

import subprocess

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
  ssh_username: ubuntu

#  These are optional
  location: VAR_REGION
#  availability_zone: VAR_AVAILABILITY_ZONE
'''


PROFILE_TEMPLATE = '''VAR_PROFILE_NAME:
    provider: VAR_PROVIDER_NAME
    ssh_interface: public_ips 
    image: VAR_IMAGE
    size: VAR_SIZE
    securitygroup: VAR_SEC_GROUP'''


AWS_CONFIG_TEMPLATE = '''[profile VAR_PROVIDER_NAME]
aws_access_key_id=VAR_APP_ID
aws_secret_access_key=VAR_APP_KEY
region=VAR_REGION
output=json
'''

class AWSDriver(base.DriverBase):

    def __init__(self, provider_name = 'aws_provider', profile_name = 'aws_profile', host_ip = '192.168.80.39', datastore = None):
        kwargs = {
            'driver_name' : 'aws', 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip
        }
        self.datastore = datastore.ConsulStore()
        self.datastore.insert('sec_groups', ['default'])

        self.image_options = ['ami-00c2af73', ]
        self.size_options = ['t1.micro', ]
        self.regions = ['ap-northeast-1', 'ap-southeast-1', 'ap-southeast-2', 'eu-west-1', 'sa-east-1', 'us-east-1', 'us-west-1', 'us-west-2']

        super(AWSDriver, self).__init__(**kwargs)
        self.aws_config = AWS_CONFIG_TEMPLATE

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
            {'name': 'Security and region'}, 
            {'name': 'Image and size'}, 
        ])

    @tornado.gen.coroutine
    def get_salt_configs(self):
        yield super(AWSDriver, self).get_salt_configs()
        for var_name in self.provider_vars: 
            self.aws_config = self.aws_config.replace(var_name, self.provider_vars[var_name])
        self.provider_name = self.provider_vars['VAR_PROVIDER_NAME']
        self.profile_name = self.profile_vars['VAR_PROFILE_NAME']

        with open('/etc/salt/cloud.providers.d/' + self.provider_name + '.conf', 'w') as f: 
            f.write(self.provider_template)
        with open('/etc/salt/cloud.profiles.d/' + self.profile_name + '.conf', 'w') as f: 
            f.write(self.profile_template)
        with open('/root/.aws/config', 'w') as f: 
            f.write(self.aws_config)

        raise tornado.gen.Return((self.provider_template, self.profile_template))

    @tornado.gen.coroutine
    def get_steps(self):
        host_info = Step('Host info')
        host_info.add_field('app_id', 'Application ID', type = 'str')
        host_info.add_field('app_key', 'Application Key', type = 'str')

        net_sec = Step('Instance info')
        net_sec.add_field('netsec_desc', 'Current connection info', type = 'description')
        net_sec.add_field('region', 'Region', type = 'options')
        net_sec.add_field('sec_group', 'Pick security group', type = 'options')

        img_size = Step('Image and size')
        img_size.add_field('img_size_desc', 'Choose an image and size for the instance. ', type = 'description')
        img_size.add_field('image', 'Choose an image', type = 'options')
        img_size.add_field('size', 'Choose size', type = 'options')

        raise tornado.gen.Return([host_info, net_sec, img_size])

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices={}
            ))
        elif step_index == 0:
            self.provider_vars['VAR_APP_ID'] = field_values['app_id']
            self.provider_vars['VAR_APP_KEY'] = field_values['app_key']

            security_groups = yield self.datastore.get('sec_groups')

            raise tornado.gen.Return(StepResult(errors=[], new_step_index=1, option_choices={                    'sec_group' : security_groups, 
                    'region' : self.regions,
            }))
        elif step_index == 1:
            self.profile_vars['VAR_SEC_GROUP'] = field_values['sec_group']
            self.provider_vars['VAR_REGION'] = field_values['region']

            raise tornado.gen.Return(StepResult(errors=[], new_step_index=2, option_choices={
                    'image' : self.image_options, 
                    'size' : self.size_options, 
            }))
        elif step_index == 2:
            self.profile_vars['VAR_IMAGE'] = field_values['image']
            self.profile_vars['VAR_SIZE'] = field_values['size'] 

            configs = yield self.get_salt_configs()


            passphrase = 'some_generated_pass'
            cmd_new_key = ['ssh-keygen', '-f', self.key_path, '-t', 'rsa', '-b', '4096', '-P', passphrase]

            cmd_aws_import  = ['aws', 'ec2', 'import-key-pair', '--key-name', self.key_name, '--public-key-material',  'file://' + self.key_path + '.pub', '--profile', 'aws_provider']

#            cmd_eval_agent = ['eval', "`ssh-agent`"]

            cmd_add_ssh = ['ssh-add', self.key_path]

            cmd_new_instance = ['salt-cloud', '--profile=' + self.profile_name, self.profile_name + '_instance']
#            with open('/tmp/cmd_line', 'w') as f: 
#                f.write(str(subprocess.list2cmdline(cmd_aws)))
#                f.write(str(subprocess.list2cmdline(cmd)))
            subprocess.call(cmd_new_key)
            subprocess.call(cmd_aws_import)
#            subprocess.call(cmd_eval_agent)
            subprocess.call(cmd_add_ssh)
            subprocess.call(cmd_new_instance)


            raise tornado.gen.Return(configs)

