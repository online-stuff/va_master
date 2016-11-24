from . import base
from .base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json, yaml
import subprocess
import libvirt
import uuid
import os
from xml.etree import ElementTree as ET
PROVIDER_TEMPLATE = ''

PROFILE_TEMPLATE = """<volume>
  <name>nino.img</name>
  <target>
    <path>/var/lib/virt/images/sparse.img</path>
    <permissions>
      <owner>107</owner>
      <group>107</group>
      <mode>0744</mode>
      <label>virt_image_t</label>
    </permissions>
  </target>
</volume>"""

PROFILE_TEMPLATE = ""

class LibVirtDriver(base.DriverBase):
    def __init__(self, provider_name = 'libvirt_provider', profile_name = 'libvirt_profile', host_ip = '192.168.80.39', path_to_images = '/etc/libvirt/qemu/'):
        kwargs = {
            'driver_name' : 'libvirt', 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip
            }
        self.path_to_images = path_to_images
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
#            images = ['xenial-server-cloudimg-amd64-disk1.img',]
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
                self.field_values['host_protocol'] = field_values['host_protocol']
            except: 
                import traceback
                traceback.print_exc()

            self.field_values['networks'] = yield self.get_networks() 
            self.field_values['images'] = yield self.get_images()
            self.field_values['sizes']= yield self.get_sizes()
            self.field_values['sec_groups'] = []

        elif step_index == 1:
            field_values['sec_group'] = None

        step_kwargs = yield super(LibVirtDriver, self).validate_field_values(step_index, field_values)
        
        raise tornado.gen.Return(StepResult(**step_kwargs))



    @tornado.gen.coroutine
    def create_minion(self, host, data):
        host_url = host['host_protocol'] + '://' + host['host_ip'] + '/system'
        conn = libvirt.open(host_url)

        old_vol = [x for x in conn.listAllDomains() if x.name() == data['image']][0]
        
        tree = ET.fromstring(old_vol.XMLDesc())
        tree.find('name').text = data['minion_name']
        tree.find('uuid').text = str(uuid.uuid4())

        #TODO get all attributes for which we want the user to have control. 
        #Or maybe we just copy the image and be done with it. 
#        tree.find('currentMemory').text = data['minion_memory']

        domain_disk = [x for x in tree.find('devices').findall('disk') if x.get('device') == 'disk'][0]
        domain_disk.find('source').attrib['file'] = data['minion_image_path']

        old_interface = tree.find('devices').find('interface')
        tree.find('devices').remove(old_interface)

        new_interface = ET.Element('interface')
        new_interface.attrib['type'] = 'network'

        network = ET.SubElement(new_interface, 'source')
        network.attrib = {'network' : 'default'}
        
        model = ET.SubElement(new_interface, 'model')
        model.attrib = {'type' : 'virtio'}

        tree.find('devices').append(new_interface)

        new_xml = ET.tostring(tree)
        try: 
            pass
            new_vol = conn.defineXML(new_xml)
            print ('Creating: ', new_vol.create())
#            print ('Starting: ', new_vol.start())
        except: 
            import traceback
            traceback.print_exc()

        yield self.create_config_drive(host, data)
        

    def create_config_drive(self, host, data):
        self.profile_vars['VAR_ROLE'] = data['role']


        config_dir = '/etc/salt/libvirt_configs/' + data['minion_name']
        instance_dir = config_dir + '/some_date_i_guess/'
        print 'Config will be : ', config_dir, ' instance dir is : ', instance_dir
        os.mkdir(config_dir)
        os.mkdir(instance_dir)

        with open(instance_dir + 'meta_data.json', 'w') as f: 
            f.write(json.dumps({'uuid' : data['fqdn']}))

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
        raise tornado.gen.Return(None)



