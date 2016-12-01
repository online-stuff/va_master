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
    def __init__(self, flavours, salt_master_fqdn, provider_name = 'libvirt_provider', profile_name = 'libvirt_profile', host_ip = '192.168.80.39', path_to_images = '/etc/libvirt/qemu/', config_path = '/etc/salt/libvirt_configs/', key_name = 'va_master_key_name', key_path = '/root/va_master_key'):
        kwargs = {
            'driver_name' : 'libvirt', 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip
            }

        self.config_path = config_path 
        self.path_to_images = path_to_images
        self.flavours = flavours
        self.salt_master_fqdn = salt_master_fqdn

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
        flavour = self.flavours[data['size']]

        print ('size is : ', data['size'])
        new_vol = yield self.create_libvirt_volume(conn, flavour['vol_capacity'], data['size'], data['minion_name'] + '-volume.qcow2')
        config_drive = yield self.create_config_drive(host, data)
        iso_image = yield self.create_iso_image(conn, data['minion_name'], config_drive)

        old_vol = [x for x in conn.listAllDomains() if x.name() == data['image']][0]     
        new_xml = yield self.create_domain_xml(old_vol.XMLDesc(), data['minion_name'], new_vol.name(), iso_image)

        try: 
            new_img = conn.defineXML(new_xml)
            new_img.setMemory = flavour['memory']
            new_img.setMaxMemory = flavour['max_memory']
            new_img.setVcpus = flavour['num_cpus']
            new_img.create()
        except: 
            import traceback
            traceback.print_exc()


    @tornado.gen.coroutine
    def create_domain_xml(self, old_xml, minion_name, vol_name, iso_name):
        print ('Generating domain xml')
        tree = ET.fromstring(old_xml)
        tree.find('name').text = minion_name
        tree.find('uuid').text = str(uuid.uuid4())

        domain_disk = [x for x in tree.find('devices').findall('disk') if x.get('device') == 'disk'][0]
        domain_disk.find('source').attrib['file'] = '/var/lib/libvirt/images/' + vol_name
        domain_disk.find('driver').attrib['type'] = 'qcow2' 
        domain_disk.find('target').attrib['bus'] = 'virtio'
        domain_disk.find('address').attrib = {
            'type':'pci',
            'domain':'0x0000',
            'bus':'0x00',
            'slot':'0x07',
            'function':'0x0',
        }

        domain_iso_disk = [x for x in tree.find('devices').findall('disk') if x.get('device') == 'cdrom'][0]
        domain_iso_disk.find('source').attrib['file'] = '/var/lib/libvirt/images/' + iso_name 


        mac = tree.find('devices').find('interface').find('mac')
        tree.find('devices').find('interface').remove(mac)
        print ('Success!')
        raise tornado.gen.Return(ET.tostring(tree))


    @tornado.gen.coroutine
    def create_iso_image(self, conn, vol_name, config_drive):
        print ('Trying to create iso. ')
        try: 
            iso_path = '/var/lib/libvirt/images/' + vol_name + '.iso'
            iso_command = ['xorrisofs', '-J', '-r', '-V', 'config_drive', '-o', iso_path, self.config_path]
            subprocess.call(iso_command)
            print ('Created iso at : ', iso_path, '. Now creating dummy volume to upload. ')
            iso_volume = yield self.create_libvirt_volume(conn, 1, 'va-small', vol_name + '-iso-vol')
            with open(iso_path, 'r') as f:
                #Libvirt documentation is terrible and I don't really know how this works. 
                def handler(stream, data, file_):
                    return file_.read(data) 
                st = conn.newStream(0)
#                iso_volume.upload(st, int(os.stat(iso_path).st_size), 0, 0)
                iso_volume.upload(st, 0, 0, 0)
                st.sendAll(handler, f)

        except: 
            import traceback
            traceback.print_exc()
        print ('Created at : ', iso_path)
        raise tornado.gen.Return(vol_name + '.iso')


    @tornado.gen.coroutine
    def create_salt_key(self, minion_name, config_dir):
        print 'Creating salt key'
        salt_command = ['salt-key', '--gen-keys=' + minion_name, '--gen-keys-dir', config_dir]
        result = subprocess.call(salt_command)
        print ('Created with result ', result)
        raise tornado.gen.Return(None)
 

    @tornado.gen.coroutine
    def create_libvirt_volume(self, conn, vol_capacity, flavour, vol_name):
        storage = [s for s in conn.listAllStoragePools() if s.name() == 'default'][0] #Maybe work with storage pools better? 
        old_vol = storage.storageVolLookupByName(flavour)
        new_vol = ET.fromstring(old_vol.XMLDesc())

        new_vol.find('name').text = vol_name
        new_vol.find('capacity').text = str(vol_capacity)
        
        new_vol = storage.createXMLFrom(ET.tostring(new_vol), old_vol)
        new_vol.resize(vol_capacity * (2**30))
        raise tornado.gen.Return(new_vol)
       

    @tornado.gen.coroutine
    def create_config_drive(self, host, data):
        print ('Creating config. ')
        minion_dir = self.config_path + data['minion_name']
        config_dir = minion_dir + '/config_drive/openstack'
        instance_dir = config_dir + '/2012-08-10/'

        os.makedirs(config_dir)
        os.makedirs(instance_dir)

        yield self.create_salt_key(data['minion_name'], minion_dir)

        pub_key = ''
        pub_key_path = minion_dir + '/' +  data['minion_name']
        with open(pub_key_path + '.pub', 'r') as f: 
            pub_key = f.read()
            pub_key = '\n'.join([x for x in pub_key.split('\n') if '--' not in x and len(x) > 2])
            pub_key_cp_cmd = ['cp',pub_key_path + '.pub', '/etc/salt/pki/minion/' + data['minion_name']]
            subprocess.call(pub_key_cp_cmd)


        pri_key = ''
        with open(minion_dir + '/' +  data['minion_name'] + '.pem', 'r') as f: 
            pri_key = f.read()
            pri_key = '\n'.join([x for x in pri_key.split('\n') if '--' not in x and len(x) > 2])


        auth_key = ''
        with open('/root/openstack_key/openstack_key_name.pem') as f: 
            auth_key = f.read()
            auth_key = '\n'.join([x for x in pri_key.split('\n') if '--' not in x and len(x) > 2])

        users_dict = {
            'fqdn' : data['instance_fqdn'], 
            'users' : [
            {
                'name' : 'root', 
                'ssh-authorized-keys': [
                    auth_key
                ]
            }], 
            'salt-minion' : {
                'conf' : {
                    'master' : self.salt_master_fqdn
                }, 
                'public_key' : pub_key,
                'private_key' : pri_key,
            }
        }


        with open(instance_dir + 'meta_data.json', 'w') as f: 
            f.write(json.dumps({'uuid' : data['instance_fqdn']}))

        with open(instance_dir + 'user_data', 'w') as f: 
            f.write(yaml.safe_dump(users_dict))

        os.symlink(instance_dir, config_dir + '/latest')

        raise tornado.gen.Return(config_dir)

