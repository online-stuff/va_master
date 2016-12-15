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

    def serialize(self):
        return {'errors': self.errors, 'new_step_index': self.new_step_index,
            'option_choices': self.option_choices}

class DriverBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def  __init__(self, driver_name,  provider_template, profile_template, provider_name, profile_name, host_ip, key_name, key_path):

        self.field_values = {
                'driver_name' : driver_name,
                'instances' : [],
                'defaults' : {},
            }
           

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
        """Returns a unique ID for this driver."""
        pass

    @abc.abstractmethod
    @tornado.gen.coroutine
    def friendly_name(self):
        """"Returns the friendly name of this driver."""
        pass

    @tornado.gen.coroutine
    def new_host_step_descriptions(self):
        raise tornado.gen.Return([
            {'name': 'Host info'},
            {'name': 'Pick a Network'},
            {'name': 'Security'}
        ])

    @tornado.gen.coroutine
    def get_salt_configs(self, skip_provider = False, skip_profile = False, base_profile = False):
        if not (self.profile_template or self.provider_template): 
            raise tornado.gen.Return(None)
        if not skip_profile: 
            self.field_values['profile_conf'] = self.profile_vars['VAR_PROFILE_NAME']
            for var_name in self.profile_vars: 
                if not (base_profile and var_name == 'VAR_PROFILE_NAME') and self.profile_vars[var_name]: 
                    self.profile_template = self.profile_template.replace(var_name, self.profile_vars[var_name])
 
        if not skip_provider: 
            self.field_values['provider_conf'] = self.provider_vars['VAR_PROVIDER_NAME'] 
            for var_name in self.provider_vars: 
                self.provider_template = self.provider_template.replace(var_name, self.provider_vars[var_name])

    @tornado.gen.coroutine
    def write_configs(self, skip_provider=False, skip_profile=False):
        if not skip_provider: 
            with open('/etc/salt/cloud.providers.d/' + self.provider_vars['VAR_PROVIDER_NAME'] + '.conf', 'w') as f: 
                f.write(self.provider_template)
        if not skip_profile:
             profile_conf_dir =  '/etc/salt/cloud.profiles.d/' + self.profile_vars['VAR_PROFILE_NAME'] + '.conf'
             self.field_values['profile_conf_dir'] = profile_conf_dir
             with open(profile_conf_dir, 'w') as f: 
                f.write(self.profile_template)


    @tornado.gen.coroutine
    def new_host_step_descriptions(self):
        raise tornado.gen.Return([
            {'name': 'Host info'},
            {'name': 'Pick a Network'},
            {'name': 'Security'}
        ])



    @tornado.gen.coroutine
    def get_steps(self):
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
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices={}
            ))

        elif step_index == 0:
            for key in field_values: 
                if field_values[key]: 
                    self.field_values[key] = field_values[key]

            self.provider_vars['VAR_USERNAME'] = field_values['username']
            self.provider_vars['VAR_PASSWORD'] = field_values['password']

            raise tornado.gen.Return({'errors':[], 'new_step_index':1,
                'option_choices':{
                    'network': self.field_values['networks'],
                    'sec_group': self.field_values['sec_groups'],
                }
            })

        elif step_index == 1:
            self.provider_vars['VAR_NETWORK_ID'] = field_values['network']
            self.profile_vars['VAR_SEC_GROUP'] = field_values['sec_group']

            self.field_values['defaults']['network'] = field_values['network']
            self.field_values['defaults']['sec_group'] = field_values['sec_group']

            raise tornado.gen.Return({
                'errors':[], 'new_step_index':2, 'option_choices':{
                    'image': self.field_values['images'],
                    'size': self.field_values['sizes'],
                }
            })
        else: 
            self.profile_vars['VAR_IMAGE'] = field_values['image']
            self.profile_vars['VAR_SIZE'] = field_values['size']

            self.field_values['defaults']['image'] = field_values['image']
            self.field_values['defaults']['size'] = field_values['size']

            yield self.get_salt_configs(base_profile = True)
            yield self.write_configs()	

            raise tornado.gen.Return({
                'errors' : [], 'new_step_index' : -1, 'option_choices':{}
            })


    @tornado.gen.coroutine
    def create_minion(self, host, data):
        profile_dir = host['profile_conf_dir']
        profile_template = ''

        with open(profile_dir) as f: 
            profile_template = f.read()


        self.profile_vars['VAR_ROLE'] = data['role']
        new_profile = data['instance_name'] + '-profile'
        self.profile_vars['VAR_PROFILE_NAME'] = new_profile
        self.profile_template = profile_template

        yield self.get_salt_configs(skip_provider = True)
        yield self.write_configs(skip_provider = True)

        #probably use salt.cloud somehow, but the documentation is terrible. 
        new_minion_cmd = ['salt-cloud', '-p', new_profile, data['instance_name']]
        minion_apply_state = ['salt', data['instance_name'], 'state.highstate']

        new_minion_values = subprocess.call(new_minion_cmd)
        new_minion_state_values = subprocess.call(minion_apply_state)

        raise tornado.gen.Return(True)


