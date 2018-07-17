try: 
    from . import base
    from .base import Step, StepResult
except: 
    import base
    from base import Step, StepResult

from base import int_to_bytes
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


BASE_CONFIG_DRIVE="""#cloud-config
hostname: VAR_INSTANCE_NAME
users:
  - name: root
    ssh-authorized-keys:
      - VAR_SSH_KEY

salt_minion:
  conf:
    startup_states: highstate
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
    def __init__(self, flavours, provider_name = 'libvirt_provider', profile_name = 'libvirt_profile', host_ip = '192.168.80.39', path_to_images = '/etc/libvirt/qemu/', config_path = '/etc/salt/libvirt_configs/', key_name = 'va_master_key', key_path = '/root/va_master_key', datastore_handler = None):
        """
            Custom init for libvirt. Does not work with saltstack, so a lot of things have to be done manually. 

            Arguments

            flavours -- A list of "flavours" defined so it can work similar to OpenStack. A flavour is just a dictionary with some values which are used to create servers. Flavours are saved in the datastore_handler, and the deploy_handler manages them. 

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
            'datastore_handler' : datastore_handler
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
        """ Works like the Base get_steps, but adds the provider_ip and provider_protocol fields. Also, there are no security groups in LibVirt, so that field is removed. """
        steps = yield super(LibVirtDriver, self).get_steps()
        steps[0].add_fields([
            ('provider_ip', 'Provider ip', 'str'),
            ('provider_protocol', 'Protocol; use qemu with Cert or qemu+tcp for no auth', 'options'),
        ])
        del steps[1].fields[2]
#        self.steps = steps

        raise tornado.gen.Return(steps)

    @tornado.gen.coroutine
    def get_networks(self):
        """ Networks are retrieved via the python api. """
        try:
            networks = self.conn.listAllNetworks()
            networks = [x.name() for x in networks]
        except: 
            import traceback
            print ('Error in get_networks in libvirt provider. ')
            traceback.print_exc()
            raise Exception("There was an error getting networks for the libvirt provider. ")
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        """ The list of security groups is empty. """
        sec_groups = ['Libvirt has no security groups']
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
            print ('Error in get_images in libvirt provider')
            traceback.print_exc()
            raise Exception("There was an error getting images for the libvirt provider. ")
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        """ Returns the flavours received from the datastore_handler. """
        raise tornado.gen.Return(self.flavours.keys())

    @tornado.gen.coroutine
    def get_provider_status(self, provider):
        """ Tries to open a connection to a provider so as to get the status. """
        try:
            provider_url = provider['provider_protocol'] + '://' + provider['provider_ip'] + '/system'
            self.conn = libvirt.open(provider_url)
        except Exception as e:
            raise tornado.gen.Return({'success' : False, 'message' : 'Error connecting to libvirt provider. ' + e.message})

        raise tornado.gen.Return({'success' : True, 'message' : ''})

    @tornado.gen.coroutine
    def get_servers(self, provider, get_servers = True, get_billing = True):
        """ Gets servers in the specified format so they can be used in get_provider_data() """
        provider_url = provider['provider_protocol'] + '://' + provider['provider_ip'] + '/system'

        try:
            conn = libvirt.open(provider_url)
        except Exception as e:
            raise tornado.gen.Return([])

        servers = []
        if not get_servers: return servers

        for x in conn.listAllDomains():
            print ('Trying to get ', x.name())
            server =  {            
                'hostname' : x.name(), 
                'ip' : 'n/a', 
                'size' : 'va-small', 
                'status' : self.libvirt_states[x.info()[0]], 
                'provider' : provider['provider_name'],
                'used_ram' : x.info()[2] / 2.0**10,
                'used_cpu': x.info()[3], 
                'used_disk' : 'n/a',

            }
            try: 
                server['used_disk'] = x.blockInfo('hda')[1] / 2.0**30
            except: 
                server['used_disk'] = 0
#                import traceback
#                print ('Cannot get used disk for server : ', x.name())
#                traceback.print_exc()
            servers.append(server)

        raise tornado.gen.Return(servers)


    @tornado.gen.coroutine
    def get_provider_data(self, provider, get_servers = True, get_billing = True):
        """ Gets provider data as specified per the Base driver. """
        provider_url = provider['provider_protocol'] + '://' + provider['provider_ip'] + '/system'

        try:
            conn = libvirt.open(provider_url)
        except Exception as e:
            provider_data = {
                'servers' : [],
                'limits' : {},
                'provider_usage' : {},
                'status' : {'success' : False, 'message' : 'Could not connect to the libvirt provider. ' + str(e)}
            }
            raise tornado.gen.Return(provider_data)


        if get_servers: 
            servers = yield self.get_servers(provider)
        else: 
            servers = []

        try:
            storage = [x for x in conn.listAllStoragePools() if x.name() == 'default'][0]
        except: 
            import traceback
            print ('Error getting storage in get_provider_data()')
            traceback.print_exc()
            raise Exception('Error getting storage for the libvirt provider. ')

        info = conn.getInfo()
        storage_info = storage.info()
        try:
            used_disk = sum([x.info()[1] for x in storage.listAllVolumes()])
            total_disk = sum([x.info()[2] for x in storage.listAllVolumes()])
        except: 
            import traceback
            print ('Error getting volumes for the default storage in get_provider_data()')
            traceback.print_exc()
            raise Exception('Error getting volumes for the default storage from the libvirt provider. ')

        print ('My servers are : ', servers)
        
        provider_usage =  {
            'max_cpus' : conn.getMaxVcpus(None), 
            'used_cpus' : sum([x['used_cpu'] for x in servers]), 
            'max_ram' : sum([x.info()[1] for x in conn.listAllDomains()]) / 2.0**10, 
            'used_ram' : sum([x['used_ram'] for x in servers]),
            'max_disk' : storage_info[1] / 2.0**30, 
            'used_disk' : storage_info[2] / 2.0**30, 
            'free_disk' : storage_info[3] / 2.0**30, 
            'max_servers' : 'n/a', 
            'used_servers' : len(servers),
        }
        provider_usage['free_cpus'] = provider_usage['max_cpus'] - provider_usage['used_cpus']
        provider_usage['free_ram'] = provider_usage['max_ram'] - provider_usage['used_ram']

        print ('And my usage : ', provider_usage)

        provider_info = {
            'servers' : servers,
            'provider_usage' : provider_usage,
            'status' : {'success' : True, 'message': ''}
        }


        raise tornado.gen.Return(provider_info)


    @tornado.gen.coroutine
    def get_provider_billing(self, provider):
        #TODO provide should have some sort of costing mechanism, and we multiply used stuff by some price. 

        total_cost = 0
        servers = yield self.get_servers(provider)
        for s in servers: 
            s['cost'] = 0
            s['estimated_cost'] = 0

#        servers.append({
#            'hostname' : 'Other Costs',
#            'ip' : '',
#            'size' : '',
#            'used_disk' : 0,
#            'used_ram' : 0,
#            'used_cpu' : 0,
#            'status' : '',
#            'cost' : total_cost,
#            'estimated_cost' : 0, 
#            'provider' : provider['provider_name'],
#        })

        total_memory = sum([x['used_ram'] for x in servers]) * 2**20
        total_memory = int_to_bytes(total_memory)
        provider['memory'] = total_memory


        for server in servers: 
            server['used_ram'] = int_to_bytes(server['used_ram'] * (2 ** 20))

        billing_data = {
            'provider' : provider, 
            'servers' : servers,
            'total_cost' : total_cost
        }
        raise tornado.gen.Return(billing_data)


    @tornado.gen.coroutine
    def server_action(self, provider, server_name, action):
        """ Performs an action via the python api. """
        provider_url = provider['provider_protocol'] + '://' + provider['provider_ip'] + '/system'

        try:
            conn = libvirt.open(provider_url)
            server = conn.lookupByName(server_name)
        except Exception as e:
            raise tornado.gen.Return({'success' : False, 'message' : 'Could not connect to provider. ' + e.message})

        server_action = {
            'delete' : server.undefine,
            'reboot' : server.reboot,
            'start' : server.create,
            'stop' : server.shutdown,
            'suspend' : server.suspend,
            'resume' : server.resume,
        }
        if action not in server_action:
            raise tornado.gen.Return({'success' : False, 'message' : 'Action not supported : ' +  action})
        try:
            success = server_action[action]()
        except Exception as e:
            raise tornado.gen.Return({'success' : False, 'message' : 'Action was not performed. ' + e.message, 'data' : {}})

        raise tornado.gen.Return({'success' : True, 'message' : ''})



    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        """ Adds the provider_protocol field, and opens a connection libvirt.conn to get info about the provider. """
        print ('Validating on step : ', step_index)
        if step_index < 0:
            protocols = ['qemu', 'qemu+tcp', 'qemu+tls']
    	    raise tornado.gen.Return(StepResult(
        		errors=[], new_step_index=0, option_choices={'provider_protocol' : protocols}
    	    ))
        elif step_index == 0:
            provider_url = field_values['provider_protocol'] + '://' + field_values['provider_ip'] + '/system'
            self.field_values['provider_ip'] = field_values['provider_ip']
            try:
                self.conn = libvirt.open(provider_url)
                print ('Opened connection to ', provider_url)
                self.field_values['provider_protocol'] = field_values['provider_protocol']
            except:
                import traceback
                print ('Error connecting to libvirt in validate_field_values()')
                traceback.print_exc()
                raise Exception('Could not connect to libvirt using the parameters - protocol: %s, provider_ip: %s. ' % (field_values['provider_protocol'], field_values['provider_ip']))

            self.field_values['networks'] = yield self.get_networks()
            self.field_values['images'] = yield self.get_images()
            self.field_values['sizes']= self.flavours.keys()
            self.field_values['sec_groups'] = []

        elif step_index == 1:
            field_values['sec_group'] = None

        step_result = yield super(LibVirtDriver, self).validate_field_values(step_index, field_values)

        raise tornado.gen.Return(step_result)

    @tornado.gen.coroutine
    def create_server(self, provider, data):
        """ 
            Instances are created manually, as there is no saltstack support. This happens by following these steps: 
            
            1. Open a connection to the libvirt provider. 
            2. Create a config drive for cloud init. What's needed for this is the salt master fqdn and the salt keys. 
            3. Clone the libvirt volume selected when adding a provider. 
            4. If a certain storage is defined when creating an server, create a new disk for it. 
            5. Create an iso image from the config drive. 
            6. Create an xml for the new server. 
            7. Define the image with the xml. 
            8. Create permanent server. 
        
        """
        print ('Creating libvirt server. ')
        data.update(self.app_fields)
        provider_url = provider['provider_protocol'] + '://' + provider['provider_ip'] + '/system'

        try:
            conn = libvirt.open(provider_url)
        except: 
            import traceback
            print ('Error connecting to libvirt at %s in create_server()' % provider_url)
            traceback.print_exc()
            raise Exception('Error connecting to libvirt with url : %s' % (provider_url))

        try:
            storage = [x for x in conn.listAllStoragePools() if x.name() == 'default'][0]
        except: 
            import traceback
            print ('Error getting the default storage pool for the libvirt provider. ')
            traceback.print_exc()
            raise Exception('Error getting the default storage pool at %s' % (provider_url))

        flavour = self.flavours[data['size']]
        storage_disk = data.get('storage_disk', 0)

        try:
            config_drive = yield self.create_config_drive(provider, data)
        except: 
            import traceback
            print ('Error creating the config drive. ')
            traceback.print_exc()
            raise Exception('Error creating the config drive for the libvirt provider. ')

        try:
            old_vol = [x for x in storage.listAllVolumes() if x.name() == data['image']][0]
            new_vol = yield self.clone_libvirt_volume(storage, flavour['vol_capacity'], old_vol, data['server_name'] + '-volume.qcow2')
            disks = [new_vol.name()]

        except: 
            import traceback
            print ('Error cloning the libvirt volume. ')
            traceback.print_exc()
            raise Exception('Error cloning the libvirt volume for the new minion. ')

        if storage_disk:
            try:
                new_disk = yield self.create_libvirt_volume(storage, storage_disk, data['server_name'] + '-disk.qcow2')
                disks.append(new_disk.name())
            except: 
                import traceback
                print ('Error creating libvirt volume with parameters storage_disk: %s, server_name: %s' % (storage_disk, data['server_name']))
                traceback.print_exc()
                raise Exception('Error creating additional libvirt volume. ')

        else: 
            disks.append(None)

        try:
            iso_image = yield self.create_iso_image(provider_url, conn, data['server_name'], config_drive, old_vol)
        except: 
            import traceback
            print ('Error creating an iso image. ')
            traceback.print_exc()
            raise Exception('Error creating the iso image for the new minion. ')


        try:
            new_xml = yield self.create_domain_xml(data['server_name'], disks, iso_image)
        except: 
            import traceback
            print ('Error generating the xml for the new minion. ')
            traceback.print_exc()
            raise Exception('Error generating the xml for the new minion. ')


        try:
            new_img = conn.defineXML(new_xml)
            new_img.setMemory = flavour['memory']
            new_img.setMaxMemory = flavour['max_memory']
            new_img.setVcpus = flavour['num_cpus']
            new_img.create()

        except: 
            import traceback
            print ('Error creating a minion from the defined XML')
            traceback.print_exc()
            raise Exception('Error creating a minion with - XML was defined but the minion was not created. ')

        self.config_drive = BASE_CONFIG_DRIVE



    @tornado.gen.coroutine
    def create_domain_xml(self, server_name, disks, iso_name):
        old_xml = DOMAIN_XML

        print ('Generating domain xml')
        tree = ET.fromstring(old_xml)
        tree.find('name').text = server_name

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
    def create_iso_image(self, provider_url, conn, vol_name, config_drive, base_volume):
        print ('Trying to create iso from dir: ', config_drive)

        try:
            iso_name = vol_name + '.iso'
            iso_path = self.config_path + iso_name
            iso_command = ['xorrisofs', '-J', '-r', '-V', 'config_drive', '-o', iso_path, config_drive]
            storage = [x for x in conn.listAllStoragePools() if x.name() == 'default'][0]

            upload_command = ['virsh', '-c', provider_url, 'vol-upload', '--pool', storage.name(), iso_name, iso_path]

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
    def create_salt_key(self, server_name, config_dir):
        print 'Creating salt key'
        salt_command = ['salt-key', '--gen-keys=' + server_name, '--gen-keys-dir', config_dir]
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
    def create_config_drive(self, provider, data):
        print ('Creating config with ', data)
        minion_dir = self.config_path + data['server_name']
        config_dir = minion_dir + '/config_drive'
        server_dir = config_dir + '/openstack/2012-08-10'

        os.makedirs(config_dir)
        os.makedirs(server_dir)

        yield self.create_salt_key(data['server_name'], minion_dir)

        pub_key = ''
        pub_key_path = minion_dir + '/' +  data['server_name']
        with open(pub_key_path + '.pub', 'r') as f:
            pub_key = f.read()
            pub_key_cp_cmd = ['cp',pub_key_path + '.pub', '/etc/salt/pki/minion/' + data['server_name']]
            pub_key_cp_master_cmd = ['cp',pub_key_path + '.pub', '/etc/salt/pki/master/minions/' + data['server_name']]

            subprocess.call(pub_key_cp_cmd)
            subprocess.call(pub_key_cp_master_cmd)

        pri_key = ''
        with open(minion_dir + '/' +  data['server_name'] + '.pem', 'r') as f:
            pri_key = f.read()

        auth_key = ''
        with open(self.key_path + '.pub') as f:
            auth_key = f.read()

        config_dict = {
            'VAR_INSTANCE_NAME' : data['server_name'],
            'VAR_IP' : self.host_ip, 
            'VAR_SSH_KEY' : auth_key,
            'VAR_PUBLIC_KEY' : '\n'.join([' ' * 4 + line for line in pub_key.split('\n')]),
            'VAR_PRIVATE_KEY' : '\n'.join([' ' * 4 + line for line in pri_key.split('\n')]),
            'VAR_ROLE' : data['role'],
#            'VAR_INSTANCE_FQDN' : data['server_name'],
        }

        for key in config_dict:
            self.config_drive = self.config_drive.replace(key, config_dict[key])

        users_dict = {
            'fqdn' : data['server_name'],
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

        with open(server_dir + '/meta_data.json', 'w') as f:
            f.write(json.dumps({'uuid' : data['server_name']}))

        with open(server_dir + '/user_data', 'w') as f:
            f.write(self.config_drive)

#        minion_dir = self.config_path + data['server_name']
#        config_dir = minion_dir + '/config_drive'
#        server_dir = config_dir + '/openstack/2012-08-10'

        os.symlink('../openstack/2012-08-10', config_dir + '/openstack/latest')

        raise tornado.gen.Return(config_dir)
