import abc
import tornado.gen

class HostStepInput(object):
    """A client input for each step of host creation."""
    def __init__(self, step_index=0, field_values=None, state=None):
        """Creates an input containing client step state.
        Parameters:
          step_index - The current client step index
          field_values - Dict of values that user entered for each field.
          state - The current state of the creation process"""
        self.step_index = step_index
        self.field_values = field_values
        self.state = state

    @tornado.gen.coroutine
    def from_handler(handler):
        pass

class HostStepOutput(object):
    """Server output for each step of host creation."""
    def __init__(self, step_index, state, errors):
        """Create a step output.
        Parameters:
          step_index - The new step
          state - A dict of values for the new state (must be serializable)
          errors - A list of strings containing error messages"""
        self.state = state
        self.errors = errors
        self.fields = []

    def new_str_field(self, fieldid, friendly_name):
        """Add string field for the next step.
        Parameters:
          fieldid - The ID of the field, will be received in `field_values` next time
          friendly_name - A human readable version of the field"""
        self.fields.append({'type': 'str', 'id': fieldid,
            'friendly_name': friendly_name})

    def new_option_field(self, fieldid, friendly_name, options):
        """An option field for the next step (multiple choices).
        Parameters:
          fieldid - The ID of the field, will be received in `field_values` next time
          friendly_name - A human readable version of the field
          options - A list of strings for possible choices."""
        self.fields.append({'type': 'str', 'id': fieldid,
            'friendly_name': friendly_name, 'options': options})

    def serialize(self):
        return {
            'step_index': self.step_index,
            'state': self.state,
            'fields': self.fields,
            'errors': self.errors
        }

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

    @abc.abstractmethod
    @tornado.gen.coroutine
    def get_salt_driver_name(self):
        """Returns the name of the salt-backed driver."""
        pass

    @abc.abstractmethod
    @tornado.gen.coroutine
    def new_host_step(self, host_step_input):
        """Executes a host step. If state and input is valid, progress to a
        new step."""
        pass

    @abc.abstractmethod
    @tornado.gen.coroutine
    def new_host_step_descriptions(self):
        """Returns the descriptions of each step required to create a new host with this
        driver."""
        pass
