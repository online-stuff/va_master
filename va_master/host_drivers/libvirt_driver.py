from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json, yaml
import subprocess
import libvirt
import os

PROVIDER_TEMPLATE = ''

PROFILE_TEMPLATE = ''

class LibVirtDriver(base.DriverBase):
    def __init__(self, provider_name = 'libvirt_provider', profile_name = 'libvirt_profile', host_ip = '192.168.80.39'):
        kwargs = {
            'driver_name' : 'libvirt', 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip
            }
        super(LibVirtDriver, self).__init__(**kwargs) 

    @tornado.gen.coroutine
    def driver_id(self):
        raise tornado.gen.Return('libvirt')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('LibVirt')


    @tornado.gen.coroutine
    def get_steps(self):
        steps = yield super(LibVirtDriver, self).get_steps()
        steps[0].add_fields([
            ('host_ip', 'Host ip', 'str'),
            ('host_protocol', 'Protocol; use qemu with Cert or qemu+tcp for no auth', 'options'),
        ])
        del steps[1].fields[2]
#        self.steps = steps

        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_networks(self):
        networks = self.conn.listAllNetworks()
        networks = [x.name() for x in networks]
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        sec_groups = []
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        try: 
            images = ['xenial-server-cloudimg-amd64-disk1.img',]
#            images = self.conn.listAllDomains()
#            images = [x.name() for x in images]
        except: 
            import traceback
            traceback.print_exc()
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        sizes = self.conn.listAllStoragePools()
        sizes = [x.name() for x in sizes]
        raise tornado.gen.Return(sizes)

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        print ('in libvirt ', step_index)
        if step_index < 0:
            protocols = ['qemu', 'qemu+tcp', 'qemu+tls']
    	    raise tornado.gen.Return(StepResult(
        		errors=[], new_step_index=0, option_choices={'host_protocol' : protocols}
    	    ))
        elif step_index == 0:
            host_url = field_values['host_protocol'] + '://' + field_values['host_ip'] + '/system'
            self.field_values['host_ip'] = field_values['host_ip'] 
            try: 
                self.conn = libvirt.open(host_url)
            except: 
                import traceback
                traceback.print_exc()

            self.field_values['networks'] = yield self.get_networks() 
            self.field_values['sec_groups'] = yield self.get_sec_groups()
            self.field_values['images'] = yield self.get_images()
            self.field_values['sizes']= yield self.get_sizes()

        elif step_index == 1:
            field_values['sec_group'] = None

        step_kwargs = yield super(LibVirtDriver, self).validate_field_values(step_index, field_values)
        
        raise tornado.gen.Return(StepResult(**step_kwargs))
      
    @tornado.gen.coroutine
    def create_minion(self, host, data):
        self.profile_vars['VAR_ROLE'] = data['role']


        config_dir = '/etc/salt/libvirt_configs/' + data['minion_name']
        instance_dir = config_dir + '/some_date_i_guess/'
        print 'Config will be : ', config_dir, ' instance dir is : ', instance_dir
#        os.mkdir(config_dir)
#        os.mkdir(instance_dir)

#        with open(instance_dir + 'meta_data.json', 'w') as f: 
#            f.write(json.dumps({'uuid' : data['fqdn']})

        users_dict = {
            'fqdn' : data['fqdn'],
            'users' : [
                {
                   'name' : {
                        'root' : {
                            'ssh-authorized-keys' : [
                                'ssh-rsa',
                            ]
                        }
                    }
                }
            ]
        }

        print (yaml.dump(users_dict))
        tornado.gen.Return(None)
#        with open(instance_dir + 'user_data') as f: 
#            f.write(yaml.dump(users_dict))

        #probably use salt.cloud somehow, but the documentation is terrible. 
        print (self.field_values, ' are values')
        arguments = [data['image'], data['fqdn'], config_dir, data['host_ip']]
        new_minion_cmd = ['./virt-boot'] + arguments
        print ('New minion: ', subprocess.list2cmdline(new_minion_cmd))
        minion_apply_state = ['salt', data['minion_name'], 'state.highstate']

#        subprocess.call(new_minion_cmd)
#        subprocess.call(minion_apply_state)


