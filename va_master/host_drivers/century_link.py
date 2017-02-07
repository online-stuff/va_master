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
    def __init__(self, flavours, salt_master_fqdn, provider_name = 'century_link_provider', profile_name = 'century_link__profile', host_ip = '192.168.80.39', key_name = 'va_master_key', key_path = '/root/va_master/va_master_key/'):
        """
            Works ok atm but needs more stuff in the future. Namely, we need the following: 
                - A way to get usage statistics. No option for this yet in the python API, so I may need to check out the REST API. 
                - Creating hosts. Driver is in the beginning stage atm, so this is for a later stage. 

            The arguments are fairly generic. Some of the more important ones are: 
            Arguments:  
                flavours -- Information about storage, CPU and other hardware for the host. We're using these to stay close to the OpenStack model. 
                salt_master_fqdn -- May be used for the config_drive if we need to generate it. Keeping it in just in case, but not used atm. 

            The locations parameter is hardcoded atm, may need to get locations in a different manner. 
        """

        self.flavours = flavours
        self.locations = [u'PrimaryDatacenter', u'au1', u'ca1', u'ca2', u'ca3', u'de1', u'gb1', u'gb3', u'il1', u'ny1', u'sg1', u'uc1', u'ut1', u'va1', u'va2', u'wa1']        

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

    def get_datacenter(self, location): 
        self.datacenter = [x for x in clc.v2.Datacenter.Datacenters() if location in x.location][0]
        return self.datacenter

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
        """ A function not in use atm, but if we need to use the clc REST API, this is how we get the token. """
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
        """ After getting the token, this is how we can get values. """
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
        clc.v2.SetCredentials(host['username'], host['password'])
        self.account = clc.v2.Account()
        self.get_datacenter(host['location'])

        servers_list = self.datacenter.Groups().Get(host['defaults']['sec_group']).Servers().Servers()
        print [x.data['details']['hostName'] for x in servers_list]
        server = [x for x in servers_list if x.data['details']['hostName'] == instance_name or x.id == instance_name] or [None]
        server = server[0]
        if not server: 
            print ('Did not find serverw with name: ', instance_name)
            raise tornado.gen.Return({'success' : False, 'message' : 'Did not find server with name: ' + instance_name})

        #post_arg is simply to cut down on code; it creates a tuple of arguments ready to be sent to the API. 
        post_arg = lambda action: ('post', 'operations/%s/servers/%s' % (self.account.alias, action), '["%s"]'% server.id)

        action_map = {
            'delete'  : ('delete', 'servers/%s/%s' % (self.account.alias, server.id), {}),
            'reboot'  : post_arg('reboot'),
            'start'   : post_arg('powerOn'),
            'stop'    : post_arg('powerOff'),
            'suspend' : post_arg('pause'),
#            'resume'  : None,
        }

        if action not in action_map: 
            raise tornado.gen.Return({'success' : False, 'message' : 'Action not supported : ' + action})
        clc.v2.API.Call(*action_map[action], debug = True)

#        success = instance_action[action](instance_name)
        raise tornado.gen.Return({'success' : True, 'message' : ''})

    @tornado.gen.coroutine
    def get_host_billing(self, host):
        get_datacenter(self, location)
        group = self.datacenter.Groups().Get(host['defaults']['sec_group'])

        billing_link = [x for x in clc.v2.API.Call(group.data['links']) if 'billing' in x['rel']]
        billing_info = clc.v2.API.Call('get', billing_link['href'])
        bililng_info = billing_info['groups'].values()[0]

        raise tornado.gen.Return({'success' : True, 'message' : billing_info})

    @tornado.gen.coroutine
    def get_instances(self, host):
        """ Gets instances from the group selected when adding the host. """
        try: 
            datacenter = self.datacenter
        except: 
            clc.v2.SetCredentials(host['username'], host['password'])
            self.account = clc.v2.Account()
            datacenter = self.datacenter = self.account.PrimaryDatacenter() 

        servers = datacenter.Groups().Get(host['defaults']['sec_group']).Servers().servers
        servers = [x.data for x in servers]

        instances =  [{
                'hostname' : x['name'],
                'ip' : None if not x['details']['ipAddresses'] else x['details']['ipAddresses'][0]['internal'],
                'size' : x['details']['storageGB'],
                'status' : x['status'],
                'host' : host['hostname'],
                'used_ram' : x['details']['memoryMB'],
                'used_cpu': x['details']['cpu'],
                'used_disk' : x['details']['diskCount'],

        } for x in servers]
        raise tornado.gen.Return(instances)


    @tornado.gen.coroutine
    def get_host_data(self, host):
        """ Gets instances properly, but doesn't yet get host_usage. """
        try:
            clc.v2.SetCredentials(host['username'], host['password'])
            self.get_datacenter(host['location'])
            self.account = clc.v2.Account()
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
        """ Works properly it seems. """
        try: 
            clc.v2.SetCredentials(host['username'], host['password'])
            self.account = clc.v2.Account()
        except: 
            raise tornado.gen.Return({'success' : False, 'message' : 'Could not connect to host: ' + e.message})
        raise tornado.gen.Return({'success' : True, 'message': ''})


    @tornado.gen.coroutine
    def get_steps(self):
        """ Uses the generic get_steps """
        steps = yield super(CenturyLinkDriver, self).get_steps()

        steps[0].add_fields([
            ('location', 'Select the location for the datacenter you want to be using, or use the Primary Datacenter. ', 'options'),
        ])

        self.steps = steps
        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_networks(self):
        """ Properly gets networks. The url variable is there in case we need the REST API. """
        networks = self.datacenter.Networks().networks
        networks = [x.name for x in networks]
#        url = '/v2-experimental/networks/{accountAlias}/{dataCenter}'
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        """ Gets the ordinary Groups, despite being called "get_sec_groups()". The name is kept the same for consistency. The url variable is there in case we need the REST API. """
        sec_groups = self.datacenter.Groups().groups
        sec_groups = [x.name for x in sec_groups]
#        url = '/v2/groups/account/id'
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        """ Gets the images. Currently, lists templates, but in the future, it will use the datastore. The url variable is there in case we need the REST API. """ 
        images = self.datacenter.Templates().templates
#        images = self.api.Call('post', 'Blueprint/GetBlueprints', {'Visibility' : 1})
        images = [x.name for x in images]       
#        url = '/v2/datacenters/account/datacenter/deploymentCapabilities'
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        """ Returns the flavours kept in the datastore. """
        sizes = self.flavours.keys()
        raise tornado.gen.Return(sizes)

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        """ Authenticates via the python API. """
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices={'location' : self.locations}
            ))
        elif step_index == 0:
#            self.host_url = field_values['host_url']
            clc.v2.SetCredentials(field_values['username'], field_values['password'])
            clc.v1.SetCredentials(field_values['username'], field_values['password'])
            self.account = clc.v2.Account() # Maybe just use v1? v2 has no endpoints for blueprints yet...

            if field_values['location'] == 'PrimaryDatacenter': 
                self.datacenter = self.account.PrimaryDatacenter()
            else: 
                self.datacenter = [x for x in clc.v2.Datacenter.Datacenters() if field_values['location'] in x.location][0]

            self.field_values['location'] = self.datacenter.location

#            clc.v1.SetCredentials(field_values['api_key'], field_values['api_secret'])
#            self.api = clc.v1.API #Needed for blueprints and other v1 actions
#            self.token = yield self.get_token(field_values)

      	step_kwargs = yield super(CenturyLinkDriver, self).validate_field_values(step_index, field_values)
        raise tornado.gen.Return(StepResult(**step_kwargs))
      
    @tornado.gen.coroutine
    def create_minion(self, host, data):
        print ('Creating minion with data: ', data)
        try: 
            clc.v2.SetCredentials(host['username'], host['password'])
            self.account = clc.v2.Account()
            self.get_datacenter(host['location'])

            flavour = self.flavours[data['size']]

            server_data = {
              "name": data['instance_name'],
              "hostName": data['instance_name'],
              "description": "Created from the VA dashboard. ",
              "groupId": self.datacenter.Groups().Get(data['sec_group']).id,
              "sourceServerId": self.datacenter.Templates().Get(data['image']).id,
              "isManagedOS": False,
              "networkId": self.datacenter.Networks().Get(data['network']).id,
              "cpu": flavour['num_cpus'],
              "memoryGB": flavour['vol_capacity'],
              "type": "standard",
              "storageType": "standard",
            }
            if data.get('storage'): 
                server_data['additionalDisks'] = [
                    {
                        'path' : 'data', 
                        'sizeGB' : data['storage'], 
                        'type' : 'raw'
                    }
                ]

            #Extra args are usually supplied by external applications. 
            server_data.update(data.get('extra_args', {}))

            success = clc.v2.API.Call('post', 'servers/%s' % (self.account.alias), json.dumps(server_data), debug = True).WaitUntilComplete()
            print ('Result was : ', success)
        except: 
            import traceback
            traceback.print_exc()
