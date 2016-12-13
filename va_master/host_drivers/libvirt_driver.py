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


#This is a dictionary which I used to parse with yaml to write a config drive. We ended up using a template instead, but we might need this sometime. 
users_dict = {
    'fqdn' : 'some.fqdn',
    'users' : [
    {
        'name' : 'root', 
        'ssh-authorized-keys': [
            'some_rsa_key'
        ]
    }], 
    'salt-minion' : {
        'conf' : {
            'master' : '192.168.80.39'
        }, 
        'public_key' : 'some_public_key',
        'private_key' : 'some_private_key',
    }
}

PROVIDER_TEMPLATE = ''

PROFILE_TEMPLATE = ''

CONFIG_DRIVE = """#cloud-config
fqdn: VAR_INSTANCE_FQDN
users:
  - name: root
    ssh-authorized-keys:
      - VAR_SSH_AUTH
salt_minion:
  conf:
    master: VAR_MASTER_FQDN
  public_key: |
VAR_PUBLIC_KEY
  private_key: |
VAR_PRIVATE_KEY
"""

DOMAIN_XML = """<domain type='kvm'>
  <name>va-master.local</name>
  <memory unit='KiB'>1048576</memory>
  <currentMemory unit='KiB'>1048576</currentMemory>
  <vcpu placement='static'>1</vcpu>
  <os>
    <type arch='x86_64' machine='pc'>hvm</type>
    <boot dev='hd'/>
  </os>
  <cpu mode='host-model'>
    <model fallback='allow'/>
  </cpu>
  <devices>
<!--    <emulator>/usr/sbin/qemu-system-x86_64</emulator> -->
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/var/lib/libvirt/images/va-master.local.qcow2'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/var/lib/libvirt/images/va-master.local.qcow2'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <source file='/var/lib/libvirt/images/va-master.local-config.iso'/>
      <target dev='hda' bus='ide'/>
      <readonly/>
    </disk>
    <interface type='network'>
      <source network='default'/>
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </interface>
<!--    <interface type='direct'>
      <source dev='HOSTNETWORKINTERFACE' mode='bridge'/> 
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x09' function='0x0'/>
    </interface> -->
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
    <input type='mouse' bus='ps2'/>
    <input type='keyboard' bus='ps2'/>
    <graphics type='vnc' port='-1' autoport='yes'>
      <listen type='address'/>
    </graphics>
    <sound model='ich6'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
    </sound>
    <video>
     <model type='qxl' ram='65536' vram='65536' vgamem='16384' heads='1' primary='yes'/>
     <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
    </video>
    <redirdev bus='usb' type='spicevmc'>
      <address type='usb' bus='0' port='1'/>
    </redirdev>
    <redirdev bus='usb' type='spicevmc'>
      <address type='usb' bus='0' port='2'/>
    </redirdev>
    <memballoon model='virtio'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </memballoon>
  </devices>
</domain>"""

BASE_VOLUME_XML = """
<volume type='file'>
  <name>VAR_NAME</name>
  <key>/var/lib/libvirt/images/VAR_NAME</key>
  <source>
  </source>
  <capacity unit='bytes'>VAR_SIZE</capacity>
  <target>
    <path>/var/lib/libvirt/images/VAR_NAME</path>
    <format type='qcow2'/>
    <permissions>
      <mode>0600</mode>
      <owner>0</owner>
      <group>0</group>
    </permissions>
  </target>
</volume>"""

class LibVirtDriver(base.DriverBase):
    def __init__(self, flavours, salt_master_fqdn, provider_name = 'libvirt_provider', profile_name = 'libvirt_profile', host_ip = '192.168.80.39', path_to_images = '/etc/libvirt/qemu/', config_path = '/etc/salt/libvirt_configs/', key_name = 'va_master_key', key_path = '/root/va_master_key'):
        kwargs = {
            'driver_name' : 'libvirt', 
            'provider_template' : PROVIDER_TEMPLATE, 
            'profile_template' : PROFILE_TEMPLATE, 
            'provider_name' : provider_name, 
            'profile_name' : profile_name, 
            'host_ip' : host_ip,
            'key_name' : key_name, 
            'key_path' : key_path,
            }
        self.conn = None
        self.config_path = config_path 
        self.path_to_images = path_to_images
        self.flavours = flavours
        self.salt_master_fqdn = salt_master_fqdn
        self.config_drive = CONFIG_DRIVE
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
            images = [x for x in self.conn.listAllStoragePools() if x.name() == 'default'][0]
            images = images.listAllVolumes()
            images = [x.name() for x in images]
        except: 
            import traceback
            traceback.print_exc()
        raise tornado.gen.Return(images)


    @tornado.gen.coroutine
    def get_host_data(self, host):
        host_url = host['host_protocol'] + '://' + host['host_ip'] + '/system'
        conn = libvirt.open(host_url)
        storage = [x for x in conn.listAllStoragePools() if x.name() == 'default'][0]
        
        info = conn.getInfo()
        host_info = {
            'instances' : conn.listDefinedDomains(),
            'limits' : {'absolute' : {
                'maxTotalCores' : conn.getMaxVcpus(None),
                'totalRamUsed' : info[1], 
                'totalCoresUsed' : info[2], 
                'totalInstancesUsed' : len(conn.listDefinedDomains()),
                'maxTotalInstances' : 'n/a'
            }}
        }

        raise tornado.gen.Return(host_info)


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
            self.field_values['sizes']= self.flavours.keys()
            self.field_values['sec_groups'] = []

        elif step_index == 1:
            field_values['sec_group'] = None

        step_kwargs = yield super(LibVirtDriver, self).validate_field_values(step_index, field_values)
        
        raise tornado.gen.Return(StepResult(**step_kwargs))




    @tornado.gen.coroutine
    def create_minion(self, host, data):
        print ('Creating minion. ')
        host_url = host['host_protocol'] + '://' + host['host_ip'] + '/system'
        conn = libvirt.open(host_url)
        storage = [x for x in conn.listAllStoragePools() if x.name() == 'default'][0]
        flavour = self.flavours[data['size']]
        storage_disk = data.get('storage_disk', 0)

        config_drive = yield self.create_config_drive(host, data)

        old_vol = [x for x in storage.listAllVolumes() if x.name() == data['image']][0]     
        new_vol = yield self.clone_libvirt_volume(storage, flavour['vol_capacity'], old_vol, data['instance_name'] + '-volume.qcow2')
        if storage_disk: 
            new_disk = yield self.create_libvirt_volume(storage, storage_disk, data['instance_name'] + '-disk.qcow2')
        print ('New disk created!. ')

        iso_image = yield self.create_iso_image(conn, data['instance_name'], config_drive, old_vol)

        new_xml = yield self.create_domain_xml(data['instance_name'], new_vol.name(), new_disk.name(), iso_image)

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
    def create_domain_xml(self, instance_name, vol_name, disk_name, iso_name):
        old_xml = DOMAIN_XML

        print ('Generating domain xml')
        tree = ET.fromstring(old_xml)
        tree.find('name').text = instance_name

        domain_disks = [x for x in tree.find('devices').findall('disk') if x.get('device') == 'disk']

        for disk_volume in zip(domain_disks, [vol_name, disk_name]):
            disk_volume[0].find('source').attrib['file'] = '/var/lib/libvirt/images/' + disk_volume[1]

        domain_iso_disk = [x for x in tree.find('devices').findall('disk') if x.get('device') == 'cdrom'][0]
        domain_iso_disk.find('source').attrib['file'] = self.config_path  + iso_name 


        mac = tree.find('devices').find('interface').find('mac')
        print ('Success, result is : ', ET.tostring(tree))
        raise tornado.gen.Return(ET.tostring(tree))


    @tornado.gen.coroutine
    def create_iso_image(self, conn, vol_name, config_drive, base_volume):
        print ('Trying to create iso from dir: ', config_drive)

        try: 
            iso_path = self.config_path +  vol_name + '.iso'
            iso_command = ['xorrisofs', '-J', '-r', '-V', 'config_drive', '-o', iso_path, config_drive]
            subprocess.call(iso_command)
            
            storage = [x for x in conn.listAllStoragePools() if x.name() == 'default'][0]
            iso_volume = yield self.create_libvirt_volume(storage, 1, vol_name + '.iso')

            with open(iso_path, 'r') as f:
                #Libvirt documentation is terrible and I don't really know how this works. 
                def handler(stream, data, file_):
                    return file_.read(data) 
                st = conn.newStream(0)
                st.sendAll(handler, f)

        except: 
            import traceback
            traceback.print_exc()
        print ('Created at : ', iso_path)
        raise tornado.gen.Return(vol_name + '.iso')


    @tornado.gen.coroutine
    def create_salt_key(self, instance_name, config_dir):
        print 'Creating salt key'
        salt_command = ['salt-key', '--gen-keys=' + instance_name, '--gen-keys-dir', config_dir]
        result = subprocess.call(salt_command)
        print ('Created with result ', result)
        raise tornado.gen.Return(None)
 

    @tornado.gen.coroutine
    def clone_libvirt_volume(self, storage, vol_capacity, old_vol, vol_name, resize = True):
        new_vol = ET.fromstring(old_vol.XMLDesc())

        print ('Creating volume ', vol_name)

        new_vol.find('name').text = vol_name
        new_vol.find('capacity').text = str(vol_capacity)
        
        new_vol = storage.createXMLFrom(ET.tostring(new_vol), old_vol)
        if resize: 
            new_vol.resize(vol_capacity * (2**30))
        raise tornado.gen.Return(new_vol)
       
    @tornado.gen.coroutine
    def create_libvirt_volume(self, storage, vol_size, vol_name):
        print ('Creating disk ', vol_name)
        try: 
            vol_xml = BASE_VOLUME_XML
           
            vol_values = {
                'VAR_SIZE' : str(vol_size * (2 ** 30)),
                'VAR_NAME' : vol_name,
            }

            for key in vol_values: 
                vol_xml = vol_xml.replace(key, vol_values[key])

            new_vol = storage.createXML(vol_xml)
        except: 
            import traceback
            traceback.print_exc()
        print ('Success!', new_vol.XMLDesc())
        raise tornado.gen.Return(new_vol)


    @tornado.gen.coroutine
    def create_config_drive(self, host, data):
        print ('Creating config. ')
        minion_dir = self.config_path + data['instance_name']
        config_dir = minion_dir + '/config_drive'
        instance_dir = config_dir + '/openstack/2012-08-10'

        os.makedirs(config_dir)
        os.makedirs(instance_dir)

        yield self.create_salt_key(data['instance_name'], minion_dir)

        pub_key = ''
        pub_key_path = minion_dir + '/' +  data['instance_name']
        with open(pub_key_path + '.pub', 'r') as f: 
            pub_key = f.read()
            pub_key_cp_cmd = ['cp',pub_key_path + '.pub', '/etc/salt/pki/minion/' + data['instance_name']]
            subprocess.call(pub_key_cp_cmd)

        pri_key = ''
        with open(minion_dir + '/' +  data['instance_name'] + '.pem', 'r') as f: 
            pri_key = f.read()

        auth_key = ''
        with open(self.key_path + '.pub') as f: 
            auth_key = f.read()


        config_dict = {
            'VAR_SSH_AUTH' : auth_key, 
            'VAR_PUBLIC_KEY' : '\n'.join([' ' * 4 + line for line in pub_key.split('\n')]),
            'VAR_PRIVATE_KEY' : '\n'.join([' ' * 4 + line for line in pri_key.split('\n')]),
            'VAR_INSTANCE_FQDN' : data['instance_name'],
            'VAR_MASTER_FQDN' : self.salt_master_fqdn 
        }

        for key in config_dict: 
            self.config_drive = self.config_drive.replace(key, config_dict[key])
        
        users_dict = {
            'fqdn' : data['instance_name'],
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
        self.config_drive = yaml.safe_dump(users_dict)

        with open(instance_dir + '/meta_data.json', 'w') as f: 
            f.write(json.dumps({'uuid' : data['instance_name']}))

        with open(instance_dir + '/user_data', 'w') as f: 
            f.write(self.config_drive)

        os.symlink(instance_dir, config_dir + '/openstack/latest')

        raise tornado.gen.Return(config_dir)

