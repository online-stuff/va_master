import salt.cloud
import abc, subprocess
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

class Step(object):
    def __init__(self, name):
        self.name = name
        self.fields = []

    def add_field(self, id_, name, type, blank = False): 
        self.fields.append({'type': type, 'id': id_, 'name': name, 'blank' : blank})

    def add_fields(self, list_of_fields):
        for field in list_of_fields: 
            self.add_field(field[0], field[1], field[2])

    def add_str_field(self, id_, name):
        self.fields.append({'type': 'str', 'id': id_, 'name': name})

    def add_options_field(self, id_, name):
        self.fields.append({'type': 'options', 'id': id_, 'name': name})

    def add_description_field(self, id_, name):
        self.fields.append({'type': 'description', 'id': id_, 'name': name})

    def validate(self, field_values):
        no_error = True
        for field in self.fields:
            if field['type'] in ('str', 'options'):
                # Check if exists at all
                if field['id'] not in field_values:
                    no_error = False
                else:
                    if len(field_values[field['id']]) < 1 and not field.get('blank'):
                        no_error = False
        return no_error

    def serialize(self):
        return {'name': self.name, 'fields': self.fields}

class StepResult(object):
    def __init__(self, errors, new_step_index, option_choices):
        self.errors = errors
        self.new_step_index = new_step_index
        self.option_choices = option_choices

    def set_option_choices(self, options):
        self.option_choices = options

    def serialize(self):
        return {'errors': self.errors, 'new_step_index': self.new_step_index,
            'option_choices': self.option_choices}

class DriverBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def  __init__(self, driver_name,  provider_template, profile_template, provider_name, profile_name, host_ip, key_name, key_path, datastore):
        """
            Initialize method for the base driver. Subclassing drivers should be overwriting this and calling it with custom arguments if they are needed. 
            Takes care of the salt key, writing salt provider and profile configurations and so on. 


            Keyword arguments: 
            driver_name -- The computer friendly driver name, for instance "my_driver". Used to find the driver when performing API requests. 
            provider_template -- A sample of how the provider configuration should look, with variable names which will be substituted from the profile_vars. 
            
            For instance, if you want to substitute an image, you should place VAR_IMAGE in the configuration, and if you're subclassing this class, the driver will replace it when generating the configuration. For custom template variables, you may need to add them to the self.provider_vars manually. 
            Example: 
                my_var = self.get_var_valule()
                self.provider_vars['MY_VAR'] = my_var
            And then you need to have MY_VAR in the provider template. 

            profile_template -- Same as provider_template, except with the profile instead. 
            provider_name -- The name of the provider for which the driver works, for instance: openstack_provider, or aws_provider. 
            profile_name -- The name of the profile. The profile configuration is generated when an instance is created, and the final name is profile_name + instance_name. 
            host_ip -- The host ip of the machine that this runs on. It can and should be taken from the datastore (the deploy_handler passes it as a default kwarg).
            key_name -- The name of the keypair that will be used to connect to created instances. Example: va_master_key
            key_path - The entire path minus the key name. Example: /root/va_master_key/, if the full path is /root/va_master_key/va_master_key.pem. 
            datastore -- A Key/Value datastore. It can be None, but drivers that use it will misbehave. 
        """

        self.field_values = {
                'driver_name' : driver_name,
                'instances' : [],
                'defaults' : {},
            }
           
        self.datastore = datastore
        self.host_ip = host_ip

        self.key_path = key_path + ('/' * (not key_path[-1] == '/')) + key_name
        self.key_name = key_name

        self.provider_vars = {'VAR_THIS_IP' : host_ip, 'VAR_PROVIDER_NAME' : provider_name, 'VAR_SSH_NAME' : key_name, 'VAR_SSH_FILE' : self.key_path + '.pem'}
        self.profile_vars = {'VAR_PROVIDER_NAME' : provider_name, 'VAR_PROFILE_NAME' : profile_name}

        self.provider_template = provider_template
        self.profile_template = profile_template
        self.client = AsyncHTTPClient()


    @abc.abstractmethod
    @tornado.gen.coroutine
    def driver_id(self):
        """
            The driver_id, recognized by the API and used in various methods. Example: my_driver
        """
        pass

    @abc.abstractmethod
    @tornado.gen.coroutine
    def friendly_name(self):
        """
            Friendly name, shown in the website. Example: My beautiful Driver
        """
        pass

    @tornado.gen.coroutine
    def new_host_step_descriptions(self):
        """
            Shows these descriptions when creating a new host. Does not need to be overwritten. 
        """
        raise tornado.gen.Return([
            {'name': 'Host info'},
            {'name': 'Pick a Network'},
            {'name': 'Security'}
        ])


    @tornado.gen.coroutine
    def get_salt_configs(self, skip_provider = False, skip_profile = False, base_profile = False):
        """
            Creates configurations for salt implementations. Does not need to be overwritten. 
            
            Arguments: 
            skip_provider -- If set to True, it will not create the provider configuration. This happens when creating an instance. 
            skip_profile -- If set to True, it will not create the profile configuration. 
            base_profile -- If set to True, it will not replace the profile name for the configuration. This happens when creating a new host to create a base profile template. This template is then read when creating a new instance, and the profile name is set. 
        """

        if not (self.profile_template or self.provider_template): 
            print ('There is no template! ')
            raise tornado.gen.Return(None)
        if not skip_profile: 
            self.field_values['profile_conf'] = self.profile_vars['VAR_PROFILE_NAME']
            for var_name in self.profile_vars: 
                print 'Trying to write : ', var_name, ' with : ', self.profile_vars[var_name]
                if not (base_profile and var_name == 'VAR_PROFILE_NAME') and self.profile_vars[var_name]: 
                    print 'Writing the value. '
                    self.profile_template = self.profile_template.replace(var_name, self.profile_vars[var_name])
                    print 'Now the template is : ', self.profile_template

 
        if not skip_provider: 
            self.field_values['provider_conf'] = self.provider_vars['VAR_PROVIDER_NAME'] 
            for var_name in self.provider_vars: 
                self.provider_template = self.provider_template.replace(var_name, self.provider_vars[var_name])

    @tornado.gen.coroutine
    def write_configs(self, skip_provider=False, skip_profile=False):
        """ 
            Writes the saved configurations. If any of the arguments are set, the corresponding configuration will not be written. Does not need to be overwritten 
        """
        print 'Template is : ', self.provider_template
        if not skip_provider and self.provider_template: 
            print ('Writing provider')
            with open('/etc/salt/cloud.providers.d/' + self.provider_vars['VAR_PROVIDER_NAME'] + '.conf', 'w') as f: 
                f.write(self.provider_template)
        if not skip_profile and self.profile_template:
             profile_conf_dir =  '/etc/salt/cloud.profiles.d/' + self.profile_vars['VAR_PROFILE_NAME'] + '.conf'
             self.field_values['profile_conf_dir'] = profile_conf_dir
             with open(profile_conf_dir, 'w') as f: 
                f.write(self.profile_template)


    @tornado.gen.coroutine
    def get_steps(self):
        """ 
            These are the arguments entered when creating a new host, split into separate steps. Does not need to be overwritten, but probably should be in order to add other types of fields. You can just call this in your implementation and add fields to whichever step you want. 
        """

        host_info = Step('Host info')
        host_info.add_fields([
            ('hostname', 'Name for the host', 'str'),
            ('username', 'Username', 'str'),
            ('password', 'Password', 'str'),
        ])


        net_sec = Step('Network & security group')
        net_sec.add_fields([
            ('netsec_desc', 'Current connection info', 'description'),
            ('network', 'Pick network', 'options'),
            ('sec_group', 'Pick security group', 'options'),
        ])


        imagesize = Step('Image & size')
        imagesize.add_fields([
            ('image', 'Image', 'options'),
            ('size', 'Size', 'options'),
        ])

        self.steps = [host_info, net_sec, imagesize]
        raise tornado.gen.Return(self.steps)

    @tornado.gen.coroutine
    def get_networks(self):
        """ 
            Gets a list of all the networks for the specific implementation. This _needs_ to be overwritten. 
        """
        networks = [] 
        raise tornado.gen.Return(networks)

    @tornado.gen.coroutine
    def get_sec_groups(self):
        """ 
            Gets a list of all the security groups for the specific implementation. This _needs_ to be overwritten. 
        """
       	sec_groups =[] 
    	raise tornado.gen.Return(sec_groups)

    @tornado.gen.coroutine
    def get_images(self):
        """ 
            Gets a list of all the images used to create instances. This _needs_ to be overwritten. 
        """
        cl = salt.cloud.CloudClient(path = '/etc/salt/cloud')
        provider_name = self.provider_vars['VAR_PROVIDER_NAME']
        images = cl.list_images(provider = provider_name)[provider_name]
        images = images[images.keys()[0]]
#        print ('Images are : ', images)
#        print ('Image one is : ', images[0])
        images = [images[x]['name'] for x in images]
        raise tornado.gen.Return(images)

    @tornado.gen.coroutine
    def get_sizes(self):
        """     
            Gets a list of all sizes (flavors) used to create instances. This _needs_ to be overwritten. 
        """
        cl = salt.cloud.CloudClient(path = '/etc/salt/cloud')
        provider_name = self.provider_vars['VAR_PROVIDER_NAME']
        sizes = cl.list_sizes(provider = provider_name)[provider_name]
        sizes = sizes[sizes.keys()[0]]
#        print ('Sizes are : ', sizes)
        sizes = [x['name'] for x in sizes]
        raise tornado.gen.Return(sizes)

    @tornado.gen.coroutine
    def instance_action(self, host, instance_name, action):
        """ 
            Performs an action for the instance. This function is a stub of how such a function _could_ look, but it depends on implementation. This _needs_ to be overwritten. 
        """
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
    def get_host_status(self, host):
        """ 
            Tries to estabilish a connection with the host. You should overwrite this method so as to properly return a negative value if the host is inaccessible. 
        """
        raise tornado.gen.Return({'success' : True, 'message': ''})


    @tornado.gen.coroutine
    def get_instances(self, host):
        """
            Gets a list of instances in the following format. The keys are fairly descriptive. used_ram is in mb, used_disk is in GB
        """
        instances =  [{
            'hostname' : '',
            'ip' : 'n/a',
            'size' : '',
            'status' : 'SHUTOFF',
            'host' : '',
            'used_ram' : 0,
            'used_cpu': 0,
            'used_disk' : 0,

        }]
        raise tornado.gen.Return(instances)
       

    @tornado.gen.coroutine
    def get_host_data(self, host, get_instances = True, get_billing = True):
        """ 
            Returns information about usage for the host and instances. The format of the data is in this function. This should be overwritten so you can see this data on the overview.
         """
        try: 
            host_data = {
                'instances' : [], 
                'host_usage' : {},
            }
            #Functions that connect to host here. 
        except Exception as e: 
            host_data['status'] = {'success' : False, 'message' : 'Could not get data. ' + e}
            raise tornado.gen.Return(host_data)

        host_usage =  {
            'max_cpus' : 0, 
            'used_cpus' : 0, 
            'max_ram' : 0,  # in MB
            'used_ram' : 0, # still in MB
            'max_disk' : 0, # in GB this time
            'used_disk' : 0, 
            'free_disk' : 0, 
            'max_instances' : 0, 
            'used_instances' : 0,
        }
        host_usage['free_cpus'] = host_usage['max_cpus'] - host_usage['used_cpus']
        host_usage['free_ram'] = host_usage['max_ram'] - host_usage['used_ram']

        instances = yield self.get_instances(self, host)

        host_info = {
            'instances' : instances,
            'host_usage' : host_usage,
            'status' : {'success' : True, 'message': ''}
        }
        raise tornado.gen.Return(host_data)

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values, options = {}):
        """ 
            Validates and saves field values entered when adding a new host. This does not need to be overwritten, but you may want to do so. 

            Arguments: 
                step_index -- The current step that is being evaluated. The first (or 0th) step is after the driver has been chosen. 
                field_values -- The results that are being evaluated. 

            When the last step has been reached (the steps are defined in the get_steps() method), the results are evaluated, and everything that has been saved to self.field_values will be saved to the datastore and then used for performing instance actions, or creating instances. Make sure to add any custom values there. 
        """
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices=options
            ))

        elif step_index == 0:
            for key in field_values: 
                if field_values[key]: 
                    self.field_values[key] = field_values[key]

            self.provider_vars['VAR_USERNAME'] = field_values['username']
            self.provider_vars['VAR_PASSWORD'] = field_values['password']

            yield self.get_salt_configs(skip_profile = True)
            yield self.write_configs(skip_profile = True)	

            print ('Now trying to get field_values. ')
    	    self.field_values['networks'] = yield self.get_networks()
            self.field_values['sec_groups'] = yield self.get_sec_groups()
            self.field_values['images'] = yield self.get_images()
            self.field_values['sizes']= yield self.get_sizes()

            options.update({
                    'network': self.field_values['networks'],
                    'sec_group': self.field_values['sec_groups'],
                })

            raise tornado.gen.Return(StepResult(
                errors = [], new_step_index =1,
                option_choices = options
            ))

        elif step_index == 1:
            self.profile_vars['VAR_NETWORK_ID'] = field_values['network']
            self.profile_vars['VAR_SEC_GROUP'] = field_values['sec_group']

            self.field_values['defaults']['network'] = field_values['network']
            self.field_values['defaults']['sec_group'] = field_values['sec_group']
            print ('Options are : ', options)
            options.update({
                    'image': self.field_values['images'],
                    'size': self.field_values['sizes'],
            })
            print ('Options is now : ', options)
            raise tornado.gen.Return(StepResult(
                errors =[], new_step_index =2, option_choices = options
            ))
        else: 
            self.profile_vars['VAR_IMAGE'] = field_values['image']
            self.profile_vars['VAR_SIZE'] = field_values['size']

            self.field_values['defaults']['image'] = field_values['image']
            self.field_values['defaults']['size'] = field_values['size']

            yield self.get_salt_configs(base_profile = True)
            yield self.write_configs()	

            raise tornado.gen.Return(StepResult(
                errors = [], new_step_index = -1, option_choices = options
            ))


    @tornado.gen.coroutine
    def create_minion(self, host, data):
        """
            Creates a minion from the host data received from the datastore, and from data received from the panel. 
            
            Arguments: 
            host - The datastore information about the host. It's important that it has the profile_conf_dir value, which is the base profile configuration. 
            data - Data about the image. It's a dictionary with the following information: 
                'role': The role with which the instance can be recognized, for instance va-directory
                'image': The image used to create the instance, for instance VAInstance
                'size': The size (flavor) used to create the instance, for instance va-small
                'new_profile': The name of the profile, for instance my-directory
                'instance_name': The name of the instance, for instance my_directory

            This method will work with proper configurations and data, but only for salt-supported technology. You _need_ to overwrite this method if the technology of your driver does not work with salt. 
        """
        profile_dir = host['profile_conf_dir']
        profile_template = ''

        with open(profile_dir) as f: 
            profile_template = f.read()

        self.profile_vars['VAR_ROLE'] = data['role']
        self.profile_vars['VAR_IMAGE'] = data['image']
        self.profile_vars['VAR_SIZE'] = data['size']
        self.profile_vars['VAR_NETWORK_ID'] = data['network'].split('|')[1]

        new_profile = data['instance_name'] + '-profile'
        self.profile_vars['VAR_PROFILE_NAME'] = new_profile
        self.profile_vars['VAR_SEC_GROUP'] = 'default'
#        self.profile_template = profile_template

        yield self.get_salt_configs(skip_provider = True)
        yield self.write_configs(skip_provider = True)

        #probably use salt.cloud somehow, but the documentation is terrible. 
        new_minion_cmd = ['salt-cloud', '-p', new_profile, data['instance_name']]
        minion_apply_state = ['salt', data['instance_name'], 'state.highstate']

        new_minion_values = subprocess.call(new_minion_cmd)
#        new_minion_state_values = subprocess.call(minion_apply_state)

        raise tornado.gen.Return(True)


