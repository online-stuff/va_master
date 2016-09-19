import abc
import tornado.gen

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
        error = False
        for field in self.fields:
            if field['type'] in ('str', 'options'):
                # Check if exists at all
                if field['id'] not in field_values:
                    error = True
            if field['type'] == 'str':
                # Check length
                val = field_values.get(field['id'], '')
                print(val)
                if len(val) < 1:
                    error = True
        return error

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
    @tornado.gen.coroutine
    def __init__(self): pass

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
