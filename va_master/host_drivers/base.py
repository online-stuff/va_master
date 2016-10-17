import abc
from tornado.gen import coroutine, Return

class Step(object):
    def __init__(self, name):
        self.name = name
        self.fields = []

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
                    if len(field_values[field['id']]) < 1:
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
    @coroutine
    def __init__(self): pass

    @abc.abstractmethod
    @coroutine
    def driver_id(self):
        """Returns a unique ID for this driver."""
        pass

    @abc.abstractmethod
    @coroutine
    def friendly_name(self):
        """"Returns the friendly name of this driver."""
        pass

    @coroutine
    @abc.abstractmethod
    def get_steps(self):
        pass

    @coroutine
    @abc.abstractmethod
    def validate_field_values(self, step_index, field_values):
        pass

    @coroutine
    @abc.abstractmethod
    def get_salt_configs(self, field_values):
        pass
