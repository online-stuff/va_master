from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json
import subprocess
import libvirt

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
  password: VAR_PASSWORD
  networks:
    - net-id: VAR_NETWORK_ID'''

PROFILE_TEMPLATE = '''VAR_PROFILE_NAME:
    provider: VAR_PROVIDER_NAME
    image: VAR_IMAGE
    size: VAR_SIZE
    minion:
        grains:
            role: VAR_ROLE
'''

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
            images = self.conn.listAllDomains()
            images = [x.name() for x in images]
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
    def create_minion(self, host):
        profile_dir = host['profile_conf_dir']
        profile_template = ''

        with open(profile_dir) as f: 
            profile_template = f.read()


        self.profile_vars['VAR_ROLE'] = data['role']
        new_profile = data['minion_name'] + '-profile'
        self.profile_vars['VAR_PROFILE_NAME'] = new_profile
        self.profile_template = profile_template

        yield self.get_salt_configs(skip_provider = True)
        yield self.write_configs(skip_provider = True)

        #probably use salt.cloud somehow, but the documentation is terrible. 
        new_minion_cmd = ['salt-cloud', '-p', new_profile, data['minion_name']]
        minion_apply_state = ['salt', data['minion_name'], 'state.highstate']

        subprocess.call(new_minion_cmd)

    #    state_file = yield get_state(state)
    #    with open('/srv/salt' + links_to_states[state], 'w') as f: 
    #        f.write(state_file)

        subprocess.call(minion_apply_state)


