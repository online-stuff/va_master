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

import clc

PROVIDER_TEMPLATE = "" 
PROFILE_TEMPLATE = "" 

class CenturyLinkDriver(base.DriverBase):
    def __init__(self, provider_name = 'century_link_provider', profile_name = 'century_link__profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master/va_master_key/'):
        kwargs = {
            'driver_name' : 'century_link_driver', 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip, 
            'key_name' : key_name, 
            'key_path' : key_path
            }
        super(CenturyLinkDriver, self).__init__(**kwargs) 

    @tornado.gen.coroutine
    def driver_id(self):
        """ Pretty simple. """
        raise tornado.gen.Return('century_link_driver')

    @tornado.gen.coroutine
    def friendly_name(self):
        """ Pretty simple. """
        raise tornado.gen.Return('Century Link')

    #Untested; may be used instead of the python api in case we want to list blueprints. 
    @tornado.gen.coroutine
    def get_token(self, field_values):
        host, username, password, host_url = (field_values['host_ip'],
            field_values['username'], field_values['password'],
            field_values['host_url'])
        url = 'https://' + host_url + '/v2/authentication/login'
        data = {
            'username': username,
            'password': password
        }
        req = HTTPRequest(url, 'POST', body=json.dumps(data), headers={
            'Content-Type': 'application/json', 
            'Host': host_url,
        })
        try:
            resp = yield self.client.fetch(req)
        except:
            import traceback
            traceback.print_exc()
            raise tornado.gen.Return((None, None))
        raise tornado.gen.Return(resp['bearerToken'])

    #Untested; may be used instead of the python api. 
    @tornado.gen.coroutine
    def get_url_value(self, url):
        full_url = 'https://' + self.host_url + url
        req = HTTPRequest(url, 'GET', body=json.dumps(data), headers={
            'Content-Type': 'application/json', 
            'Host': host_url,
            'Authorization' : self.token
        })
        try:
            resp = yield self.client.fetch(req)
        except:
            import traceback
            traceback.print_exc()
            raise tornado.gen.Return(None)
        raise tornado.gen.Return(resp)

    @tornado.gen.coroutine
    def instance_action(self, host, instance_name, action):
        
        instance_action = {
            'delete' : 'delete_function', 
            'reboot' : 'reboot_function', 
            'start' : 'start_function', 
            'stop' : 'stop_function', 
        }
        if action not in instance_action: 
            raise tornado.gen.Return({'success' : False, 'message' : 'Action not supported : ' + action})

        success = instance_action[action](instance_name)
        raise tornado.gen.Return({'success' : True, 'message' : ''})


    @tornado.gen.coroutine
    def get_instances(self, host):
        servers = self.datacenter.Groups().get(host['defaults']['sec_group'])
        servers = [x.data for x in servers]

        instances =  [{
                'hostname' : x['name'],
                'ip' : x['details']['ipAddresses'],
                'size' : x['details']['storageGB'],
                'status' : 'SHUTOFF',
                'host' : host['hostname'],
                'used_ram' : x['details']['memoryMB'],
                'used_cpu': x['details']['cpu'],
                'used_disk' : x['details']['diskCount'],

        } for x in servers]
        raise tornado.gen.Return(instances)


    @tornado.gen.coroutine
    def get_host_data(self, host):
        try:
            clc.v2.SetCredentials(host['username'], host['password'])
            self.account = clc.v2.Account()
            seld.datacenter = self.account.PrimaryDatacenter() 
            instances = yield self.get_instances(host)
            host_data = {
                'instances' : instances, 
                'host_usage' : {
                    'max_cpus' : 'n/a',
                    'used_cpus' : sum([x['used_cpu'] for x in instances]),
                    'free_cpus' : 'n/a',
                    'max_ram' : 'n/a',
                    'used_ram' : sum([x['used_ram'] for x in instances]),
                    'free_ram' : 'n/a',
                    'max_disk' : 'n/a',
                    'used_disk' : sum([x['used_disk'] for x in instances]),
                    'free_disk' : 'n/a',
                    'max_instances' : 'n/a',
                    'used_instances' : len(instances),
                    'free_instances' :'n/a' 
                },
            }
            #Functions that connect to host here. 
        except Exception as e: 
            import traceback
            traceback.print_exc()
            host_data = {
                'instances' : [], 
                'host_usage' : {},
                'status' : {'success' : False, 'message' : 'Could not connect to the libvirt host. ' + e.message}
            }
            raise tornado.gen.Return(host_data)
        raise tornado.gen.Return(host_data)

    @tornado.gen.coroutine
    def get_host_status(self, host):
        try: 
            clc.v2.SetCredentials(host['username'], host['password'])
            self.account = clc.v2.Account()
        except: 
            raise tornado.gen.Return({'success' : False, 'message' : 'Could not connect to host: ' + e.message})
        raise tornado.gen.Return({'success' : True, 'message': ''})


    @tornado.gen.coroutine
    def get_steps(self):
        steps = yield super(CenturyLinkDriver, self).get_steps()

        self.steps = steps
        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_networks(self):
        
        networks = self.datacenter.Networks().networks
        networks = [x.name for x in networks]
#        url = '/v2-experimental/networks/{accountAlias}/{dataCenter}'
#        network = ['sadf']
#        networks = yield self.get_rest_value(url)
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        
        sec_groups = self.datacenter.Groups().groups
        sec_groups = [x.name for x in sec_groups]
#        sec_groups = self.datacenter.Groups()
#        url = '/v2/groups/account/id'
#        sec_groups = ['list', 'of', 'security', 'groups']
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
 
        images = self.datacenter.Templates().templates
        images = [x.name for x in images]       
#        url = '/v2/datacenters/account/datacenter/deploymentCapabilities'
#        images = yield self.get_rest_value(url)
#       images = ['list', 'of', 'images']
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        
        sizes = ['list', 'of', 'sizes']
        raise tornado.gen.Return(sizes)

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices={}
            ))
        elif step_index == 0:
#            self.host_url = field_values['host_url']
            clc.v2.SetCredentials(field_values['username'], field_values['password'])
            self.account = clc.v2.Account()
            self.datacenter = self.account.PrimaryDatacenter()
#            self.token = yield self.get_token(field_values)

      	step_kwargs = yield super(CenturyLinkDriver, self).validate_field_values(step_index, field_values)
        raise tornado.gen.Return(StepResult(**step_kwargs))
      
    @tornado.gen.coroutine
    def create_minion(self, host, data):
        self.datacenter = clc.v2.Datacenter()
        clc.v2.Server.Create(
            name = data['instance_name'], 
            template = self.datacenter.Templates(), 
            group_id = self.datacenter.Groups(),
            network_id = self.datacenter.Networks()
        )
