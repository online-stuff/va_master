from . import base
import tornado.gen

class OpenStackDriver(base.DriverBase):
    def __init__(self): pass

    @tornado.gen.coroutine
    def driver_id(self):
        raise tornado.gen.Return('openstack')

    @tornado.gen.coroutine
    def friendly_name(self):
        raise tornado.gen.Return('OpenStack')

    @tornado.gen.coroutine
    def get_salt_driver_name(self):
        raise tornado.gen.Return('nova')

    @tornado.gen.coroutine
    def new_host_step_descriptions(self):
        raise tornado.gen.Return([
            {'name': 'Host info'},
            {'name': 'Pick a Network'},
            {'name': 'Security'}
        ])

    @tornado.gen.coroutine
    def new_host_step(self, host_step_input):
        if host_step_input.step_index == 0:
            out = base.HostStepOutput(step_index=1, state={
            }, errors=[])
            out.add_str_field('hostname', 'Hostname')
            out.add_str_field('username', 'Username')
            out.add_str_field('password', 'Password')
            out.add_str_field('tenant', 'Tenant')
            raise tornado.gen.Return(out)
        else:
            if host_step_input.step_index == 1:
                out = base.HostStepOutput(state={
                    'step_index': 2
                }, errors=[])
                raise tornado.gen.Return(out)
            raise tornado.gen.Return(0)
