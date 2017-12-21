from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json

import subprocess

import boto3

PROVIDER_TEMPLATE = '''VAR_PROVIDER_NAME:
  id: VAR_AWS_ACCESS_KEY_ID 
  key: VAR_AWS_SECRET_ACCESS_KEY
  keyname: VAR_SSH_NAME
  private_key: VAR_SSH_FILE
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

    def __init__(self, provider_name = 'aws_provider', profile_name = 'aws_profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore_handler = None):
        kwargs = {
            'driver_name' : 'aws', 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip,
            'key_name' : key_name,
            'key_path' : key_path, 
            'datastore_handler' : datastore_handler,
        }
        self.aws_client = None

        self.image_options = ['ami-00c2af73', ]
        self.size_options = ['t1.micro', ]
        self.regions = ['ap-northeast-1', 'ap-southeast-1', 'ap-southeast-2', 'eu-west-1', 'sa-east-1', 'us-east-1', 'us-west-1', 'us-west-2']

        super(AWSDriver, self).__init__(**kwargs)
        self.aws_config = AWS_CONFIG_TEMPLATE


    def get_client(self, provider):
        session = boto3.session.Session(aws_access_key_id = provider['aws_access_key_id'], aws_secret_access_key = provider['aws_secret_access_key'], region_name = provider['region'])
        client = session.client('ec2')
        self.aws_client = client
        return client

    @tornado.gen.coroutine
    def driver_id(self):
        raise tornado.gen.Return('aws')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('AWS')

    @tornado.gen.coroutine
    def new_provider_step_descriptions(self):
        raise tornado.gen.Return([
            {'name': 'Host Info'},
            {'name': 'Security and region'}, 
            {'name': 'Image and size'}, 
        ])

    @tornado.gen.coroutine
    def get_steps(self):
        """ Adds a provider_ip, tenant and region field to the first step. These are needed in order to get OpenStack values. """

        steps = yield super(AWSDriver, self).get_steps()
        steps[0].add_fields([
            ('region', 'Region', 'options'),
            ('aws_access_key_id', 'AWS access key IDD', 'str'),
            ('aws_secret_access_key', 'AWS secret access key', 'str'),
        ])
        self.steps = steps
        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_images(self):
        #ec2 hiccups at images for the moment, no idea why
        #images_result = self.aws_client.describe_images()
        #images = images_result['Images']
        return self.image_options

    @tornado.gen.coroutine
    def get_sizes(self):
        #TODO find a way to list sizes properly
        return self.size_options
    
    @tornado.gen.coroutine
    def get_sec_groups(self):
        sec_result = self.aws_client.describe_security_groups()
        print ('Sec result is : ', sec_result)
        sec_groups = sec_result['SecurityGroups']
        return [x['GroupName'] for x in sec_groups]
   
    @tornado.gen.coroutine
    def get_networks(self):
        net_result = self.aws_client.describe_network_interfaces()
        print ('Net result is : ', net_result)
        networks = net_result['NetworkInterfaces'] or ['default']
        return networks

    @tornado.gen.coroutine
    def get_servers(self, provider):
        client = self.get_client(provider)
        result = client.describe_instances()
        servers = result['Reservations']
        raise tornado.gen.Return(servers)

        #TODO servers are returned in a format I don't yet know, need to create some so I can test this. 
        #Should be like this: 
#        servers = [
#            {
#                'hostname' : 'name', 
#                'ipv4' : 'ipv4', 
#                'local_gb' : 0, 
#                'memory_mb' : 0, 
#                'status' : 'n/a', 
#            } for x in data['servers']
#        ]


    @tornado.gen.coroutine
    def get_provider_data(self, provider, get_servers = True, get_billing = True):
        client = self.get_client(provider)
        provider_usage = {
            'total_disk_usage_gb' : 0, 
            'current_disk_usage_mb' : 0, 
            'cpus_usage' : 0
        }
        servers = []
        if get_servers:
            servers = yield self.get_servers(provider)
        provider_data = {
            'servers' : servers, 
            'provider_usage' : provider_usage, 
            'status' : {'success' : True, 'message' : ''},
        }
        raise tornado.gen.Return(provider_data)

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        """ Uses the base driver method, but adds the region tenant and identity_url variables, used in the configurations. """
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices={'region' : self.regions,}
            ))
        elif step_index == 0:
            self.provider_vars['VAR_REGION'] = field_values['region']
            provider = {}
            for x in ['aws_access_key_id', 'aws_secret_access_key', 'region']:
                provider[x] = field_values[x]
                self.provider_vars['VAR_' + x.upper()] = field_values[x]

            self.get_client(provider)
            self.field_values.update(provider)
        try:
            step_result = yield super(AWSDriver, self).validate_field_values(step_index, field_values)
        except:
            import traceback
            traceback.print_exc()
        raise tornado.gen.Return(step_result)

#            Probablt not important right now but might come in handy. 
#            cmd_aws_import  = ['aws', 'ec2', 'import-key-pair', '--key-name', self.key_name, '--public-key-material',  'file://' + self.key_path + '.pub', '--profile', 'aws_provider']

