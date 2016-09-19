from . import base
from .base import Step, StepResult
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
    def new_host_step_descriptions(self):
        raise tornado.gen.Return([
            {'name': 'Host info'},
            {'name': 'Pick a Network'},
            {'name': 'Security'}
        ])

    @tornado.gen.coroutine
    def get_steps(self):
        host_info = Step('Host info')
        host_info.add_str_field('hostname', 'Hostname')
        host_info.add_str_field('username', 'Username')
        host_info.add_str_field('password', 'Password')
        host_info.add_str_field('tenant', 'Tenant')

        net_sec = Step('Network & security group')
        net_sec.add_options_field('network', 'Pick network')
        net_sec.add_options_field('sec_group', 'Pick security group')

        ssh = Step('SSH key')
        ssh.add_description_field('description', 'Import this keypair into Openstack')
        ssh.add_str_field('private_key_name', 'Name of key')

        imagesize = Step('Image & size')
        imagesize.add_options_field('image', 'Image')
        imagesize.add_options_field('size', 'Size')
        raise tornado.gen.Return([host_info, net_sec, ssh, imagesize])

    @tornado.gen.coroutine
    def validate_field_values(self, step_index, field_values):
        if step_index < 0:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=0, option_choices={}
            ))
        elif step_index == 0:
            networks = ['net-sd1easd', 'net-sdf83']
            sec_groups = ['my group 1', 'my_group_2']
            url = 'http://%s/v2.0'
            raise tornado.gen.Return(StepResult(errors=[], new_step_index=1,
                option_choices={
                    'network': networks,
                    'sec_group': sec_groups,
                }
            ))
        elif step_index == 1:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=2, option_choices={
                    'description': 'sdfaj*75%$$$xlLueHx'
                }
            ))
        elif step_index == 2:
            raise tornado.gen.Return(StepResult(
                errors=[], new_step_index=3, option_choices={
                    'image': ['img-1', 'img-2'],
                    'size': ['va-small', 'va-med']
                }
            ))
