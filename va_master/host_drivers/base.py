import abc
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

class Step(object):
    def __init__(self, name):
        self.name = name
        self.fields = []

    def add_field(self, id_, name, type, blank = False): 
        self.fields.append({'type': type, 'id': id_, 'name': name, 'blank' : blank})

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
    def  __init__(self, provider_template, profile_template, provider_vars, profile_vars):
        self.provider_template = provider_template
        self.profile_template = profile_template
        self.provider_vars = provider_vars
        self.profile_vars = profile_vars
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
    @abc.abstractmethod
    def get_steps(self):
        pass

    @tornado.gen.coroutine
    @abc.abstractmethod
    def validate_field_values(self, step_index, field_values):
        pass

    @tornado.gen.coroutine
#    @abc.abstractmethod
    def get_salt_configs(self):
        for var_name in self.profile_vars: 
            self.profile_template = self.profile_template.replace(var_name, self.profile_vars[var_name])
        for var_name in self.provider_vars: 
            self.provider_template = self.provider_template.replace(var_name, self.provider_vars[var_name])
