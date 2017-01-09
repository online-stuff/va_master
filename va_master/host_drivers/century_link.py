from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json
import subprocess

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from salt.cloud.clouds import nova

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
        raise tornado.gen.Return('century_link_driver')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('Century Link')

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
    def get_steps(self):
        steps = yield super(CenturyLinkDriver, self).get_steps()

        steps[0].add_fields([
            ('host_url', 'Host url', 'str'),
        ])

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
                errors=[], new_step_index=0, option_choices={}
            ))
        elif step_index == 0:
            self.host_url = field_values['host_url']
            self.token = yield self.get_token(field_values)

            self.field_values['networks'] = yield self.get_networks() 
            self.field_values['sec_groups'] = yield self.get_sec_groups()
            self.field_values['images'] = yield self.get_images()
            self.field_values['sizes']= yield self.get_sizes()


       	step_kwargs = yield super(CenturyLinkDriver, self).validate_field_values(step_index, field_values)
        raise tornado.gen.Return(StepResult(**step_kwargs))
       
