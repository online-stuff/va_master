try: 
    from . import base
    from .base import Step, StepResult
except: 
    import base
    from base import Step, StepResult
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.gen
import json, yaml
import subprocess
#import libvirt
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


BASE_CONFIG_DRIVE="""#cloud-config
hostname: VAR_INSTANCE_NAME
users:
  - name: root
    ssh-authorized-keys:
      - VAR_SSH_KEY

salt_minion:
  conf:
    master: VAR_IP
    grains:
      role: VAR_ROLE
  private_key: |
VAR_PRIVATE_KEY
  public_key: |
VAR_PUBLIC_KEY
"""




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


DISK_XML = """<disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/var/lib/libvirt/images/va-master.local.qcow2'/>
      <target dev='vda' bus='virtio'/>
    </disk>
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
    <format type='VAR_FORMAT'/>
    <permissions>
      <mode>0600</mode>
      <owner>0</owner>
      <group>0</group>
    </permissions>
  </target>
</volume>"""

class LibVirtDriver(base.DriverBase):
    def __init__(self, flavours, provider_name = 'libvirt_provider', profile_name = 'libvirt_profile', host_ip = '192.168.80.39', path_to_images = '/etc/libvirt/qemu/', config_path = '/etc/salt/libvirt_configs/', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore = None):
        """
            Custom init for libvirt. Does not work with saltstack, so a lot of things have to be done manually. 

            Arguments

            flavours -- A list of "flavours" defined so it can work similar to OpenStack. A flavour is just a dictionary with some values which are used to create instances. Flavours are saved in the datastore, and the deploy_handler manages them. 

            The rest are similar to the Base driver arguments. 

            The LibVirt driver defines a property libvirt_states, which maps LibVirt states to OpenStack states where possible.  
        """
        kwargs = {
            'driver_name' : 'libvirt',
            'provider_template' : PROVIDER_TEMPLATE,
            'profile_template' : PROFILE_TEMPLATE,
            'provider_name' : provider_name,
            'profile_name' : profile_name,
            'host_ip' : host_ip,
            'key_name' : key_name,
            'key_path' : key_path,
            'datastore' : datastore
            }
        self.conn = None
        self.config_path = config_path
        self.path_to_images = path_to_images
        self.flavours = flavours
        self.config_drive = BASE_CONFIG_DRIVE

        self.libvirt_states = ['no_state', 'ACTIVE', 'blocked', 'PAUSED', 'shutdown', 'SHUTOFF', 'crashed', 'SUSPENDED']


        super(LibVirtDriver, self).__init__(**kwargs)


    @tornado.gen.coroutine
    def driver_id(self):
        """ Pretty simple. """
        raise tornado.gen.Return('libvirt')

    @tornado.gen.coroutine
    def friendly_name(self):
        """ Pretty simple. """
        raise tornado.gen.Return('LibVirt')


    @tornado.gen.coroutine
    def get_steps(self):
        """ Works like the Base get_steps, but adds the host_ip and host_protocol fields. Also, there are no security groups in LibVirt, so that field is removed. """
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
        """ Networks are retrieved via the python api. """
        networks = self.conn.listAllNetworks()
        networks = [x.name() for x in networks]
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        """ The list of security groups is empty. """
        sec_groups = []
        raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        """ Lists all volumes from the default storage pool. """
        try:
            images = [x for x in self.conn.listAllStoragePools() if x.name() == 'default'][0]
            images = images.listAllVolumes()
            images = [x.name() for x in images]
        except:
            import traceback
            traceback.print_exc()
        print ('Got images : ', images)
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        """ Returns the flavours received from the datastore. """
        raise tornado.gen.Return(self.flavours.keys())

    @tornado.gen.coroutine
    def get_host_status(self, host):
        """ Tries to open a connection to a host so as to get the status. """
        try:
            host_url = host['host_protocol'] + '://' + host['host_ip'] + '/system'
            self.conn = libvirt.open(host_url)
        except Exception as e:
            raise tornado.gen.Return({'success' : False, 'message' : 'Error connecting to libvirt host. ' + e.message})

        raise tornado.gen.Return({'success' : True, 'message' : ''})

    @tornado.gen.coroutine
    def get_instances(self, host, get_instances = True, get_billing = True):
        """ Gets instances in the specified format so they can be used in get_host_data() """
        host_url = host['host_protocol'] + '://' + host['host_ip'] + '/system'

        try:
            conn = libvirt.open(host_url)
        except Exception as e:
            raise tornado.gen.Return([])

        instances = []
        if not get_instances: return instances

        for x in conn.listAllDomains():
            print ('Trying to get ', x.name)
            instance =  {            
                'hostname' : x.name(), 
                'ip' : 'n/a', 
                'size' : 'va-small', 
                'status' : self.libvirt_states[x.info()[0]], 
                'host' : host['hostname'],
                'used_ram' : x.info()[2] / 2.0**10,
                'used_cpu': x.info()[3], 
                'used_disk' : 'n/a',

            }
            try: 
                instance['used_disk'] = x.blockInfo('hda')[1] / 2.0**30
            except: 
                instance['used_disk'] = 0
#                import traceback
#                print ('Cannot get used disk for instance : ', x.name())
#                traceback.print_exc()
            instances.append(instance)

        raise tornado.gen.Return(instances)


    @tornado.gen.coroutine
    def get_host_data(self, host, get_instances = True, get_billing = True):
        """ Gets host data as specified per the Base driver. """
        host_url = host['host_protocol'] + '://' + host['host_ip'] + '/system'

        try:
            conn = libvirt.open(host_url)
        except Exception as e:
            host_data = {
                'instances' : [],
                'limits' : {},
                'host_usage' : {},
                'status' : {'success' : False, 'message' : 'Could not connect to the libvirt host. ' + e}
            }
            raise tornado.gen.Return(host_data)


        if get_instances: 
            instances = yield self.get_instances(host)
        else: 
            instances = []

        storage = [x for x in conn.listAllStoragePools() if x.name() == 'default'][0]

        info = conn.getInfo()
        storage_info = storage.info()
        used_disk = sum([x.info()[1] for x in storage.listAllVolumes()])
        total_disk = sum([x.info()[2] for x in storage.listAllVolumes()])

        
        host_usage =  {
            'max_cpus' : conn.getMaxVcpus(None), 
            'used_cpus' : sum([x['used_cpu'] for x in instances]), 
            'max_ram' : sum([x.info()[1] for x in conn.listAllDomains()]) / 2.0**10, 
            'used_ram' : sum([x['used_ram'] for x in instances]),
            'max_disk' : storage_info[1] / 2.0**30, 
            'used_disk' : storage_info[2] / 2.0**30, 
            'free_disk' : storage_info[3] / 2.0**30, 
            'max_instances' : 'n/a', 
            'used_instances' : len(instances),
      }
        host_usage['free_cpus'] = host_usage['max_cpus'] - host_usage['used_cpus']
        host_usage['free_ram'] = host_usage['max_ram'] - host_usage['used_ram']

        host_info = {
            'instances' : instances,
            'host_usage' : host_usage,
            'status' : {'success' : True, 'message': ''}
        }


        raise tornado.gen.Return(host_info)


    @tornado.gen.coroutine
    def instance_action(self, host, instance_name, action):
        """ Performs an action via the python api. """
        host_url = host['host_protocol'] + '://' + host['host_ip'] + '/system'

        try:
            conn = libvirt.open(host_url)
            instance = conn.lookupByName(instance_name)
        except Exception as e:
            raise tornado.gen.Return({'success' : False, 'message' : 'Could not connect to host. ' + e.message})

        instance_action = {
            'delete' : instance.undefine,
            'reboot' : instance.reboot,
            'start' : instance.create,
            'stop' : instance.shutdown,
            'suspend' : instance.suspend,
            'resume' : instance.resume,
        }
        if action not in instance_action:
            raise tornado.gen.Return({'success' : False, 'message' : 'Action not supported : ' +  action})
        try:
            success = instance_action[action]()
        except Exception as e:
            raise tornado.gen.Return({'success' : False, 'message' : 'Action was not performed. ' + e.message})

        raise tornado.gen.Return({'success' : True, 'message' : ''})



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        """ Adds the host_protocol field, and opens a connection libvirt.conn to get info about the host. """
        print ('Validating on step : ', step_index)
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
                print ('Opened connection to ', host_url)
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
        """ 
            Instances are created manually, as there is no saltstack support. This happens by following these steps: 
            
            1. Open a connection to the libvirt host. 
            2. Create a config drive for cloud init. What's needed for this is the salt master fqdn and the salt keys. 
            3. Clone the libvirt volume selected when adding a host. 
            4. If a certain storage is defined when creating an instance, create a new disk for it. 
            5. Create an iso image from the config drive. 
            6. Create an xml for the new instance. 
            7. Define the image with the xml. 
            8. Create permanent instance. 
        
        """
        print ('Creating minion. ')
        host_url = host['host_protocol'] + '://' + host['host_ip'] + '/system'
        conn = libvirt.open(host_url)
        storage = [x for x in conn.listAllStoragePools() if x.name() == 'default'][0]
        flavour = self.flavours[data['size']]
        storage_disk = data.get('storage_disk', 0)

        config_drive = yield self.create_config_drive(host, data)

        old_vol = [x for x in storage.listAllVolumes() if x.name() == data['image']][0]
        new_vol = yield self.clone_libvirt_volume(storage, flavour['vol_capacity'], old_vol, data['instance_name'] + '-volume.qcow2')
        disks = [new_vol.name()]
        if storage_disk:
            new_disk = yield self.create_libvirt_volume(storage, storage_disk, data['instance_name'] + '-disk.qcow2')
            disks.append(new_disk.name())
        else: 
            disks.append(None)
        print ('New disk created!. ')

        iso_image = yield self.create_iso_image(host_url, conn, data['instance_name'], config_drive, old_vol)

        new_xml = yield self.create_domain_xml(data['instance_name'], disks, iso_image)

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
    def create_domain_xml(self, instance_name, disks, iso_name):
        old_xml = DOMAIN_XML

        print ('Generating domain xml')
        tree = ET.fromstring(old_xml)
        tree.find('name').text = instance_name

        devices = tree.find('devices')
        domain_disks = [x for x in devices.findall('disk') if x.get('device') == 'disk']


        domain_disks[0].find('source').attrib['file'] = '/var/lib/libvirt/images/' + disks[0]
        if disks[1]: 
            domain_disks[1].find('source').attrib['file'] = '/var/lib/libvirt/images/' + disks[1]
        else: 
            devices.remove(devices[1])

        domain_iso_disk = [x for x in tree.find('devices').findall('disk') if x.get('device') == 'cdrom'][0]

        #Patekata mu e kaj pool-ot kaj sto e uploadiran volume 08.02.2017
        domain_iso_disk.find('source').attrib['file'] = '/var/lib/libvirt/images/' + iso_name #self.config_path  + iso_name


        mac = tree.find('devices').find('interface').find('mac')
        print ('Success, result is : ', ET.tostring(tree))
        raise tornado.gen.Return(ET.tostring(tree))


    @tornado.gen.coroutine
    def create_iso_image(self, host_url, conn, vol_name, config_drive, base_volume):
        print ('Trying to create iso from dir: ', config_drive)

        try:
            iso_name = vol_name + '.iso'
            iso_path = self.config_path + iso_name
            iso_command = ['xorrisofs', '-J', '-r', '-V', 'config_drive', '-o', iso_path, config_drive]
            storage = [x for x in conn.listAllStoragePools() if x.name() == 'default'][0]

            upload_command = ['virsh', '-c', host_url, 'vol-upload', '--pool', storage.name(), iso_name, iso_path]

            iso_volume = yield self.create_libvirt_volume(storage, 1, iso_name)

            subprocess.call(iso_command)
            subprocess.call(upload_command)
            with open(iso_path, 'r') as f:
                #Libvirt documentation is terrible and I don't really know how this works.
                def handler(stream, data, file_):
                    return file_.read(data)
                st = conn.newStream(0)
#                st.sendAll(handler, f)

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
                'VAR_FORMAT' : 'raw'
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
            'VAR_INSTANCE_NAME' : data['instance_name'],
            'VAR_IP' : self.host_ip, 
            'VAR_SSH_KEY' : auth_key,
            'VAR_PUBLIC_KEY' : '\n'.join([' ' * 4 + line for line in pub_key.split('\n')]),
            'VAR_PRIVATE_KEY' : '\n'.join([' ' * 4 + line for line in pri_key.split('\n')]),
            'VAR_ROLE' : data['role'],
#            'VAR_INSTANCE_FQDN' : data['instance_name'],
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
                    'master' : self.host_ip
                },
                'public_key' : pub_key,
                'private_key' : pri_key,
            }
        }
#        self.config_drive = yaml.safe_dump(users_dict)

        with open(instance_dir + '/meta_data.json', 'w') as f:
            f.write(json.dumps({'uuid' : data['instance_name']}))

        with open(instance_dir + '/user_data', 'w') as f:
            f.write(self.config_drive)

        os.symlink(instance_dir, config_dir + '/openstack/latest')

        raise tornado.gen.Return(config_dir)
