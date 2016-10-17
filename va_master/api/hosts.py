from .login import auth_only
from tornado.gen import coroutine, Return
import json

def initialize(handler):
    handler.add_get_endpoint('hosts', list_hosts)
    handler.add_get_endpoint('drivers', list_drivers)
    handler.add_post_endpoint('hosts/new/validate_fields', validate_newhost_fields)

@auth_only
@coroutine
def list_hosts(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    handler.json({'hosts': hosts})

@auth_only
@coroutine
def list_drivers(handler):
    """GET /api/drivers"""
    drivers = yield handler.config.deploy_handler.get_drivers()
    out = {'drivers': []}
    for driver in drivers:
        driver_id = yield driver.driver_id()
        name = yield driver.friendly_name()
        steps = yield driver.get_steps()
        steps = [x.serialize() for x in steps]
        out['drivers'].append({'id': driver_id,
            'friendly_name': name, 'steps': steps})
    handler.json(out)

@auth_only
@coroutine
def validate_newhost_fields(handler):
    ok = True
    try:
        body = json.loads(handler.request.body)
        driver_id = str(body['driver_id'])
        field_values = dict(body['field_values'])
        step_index = int(body['step_index'])
    except:
        handler.json({'error': 'bad_body'}, 400)
        raise Return(None)

    found_driver = yield handler.config.deploy_handler.get_driver_by_id(driver_id)
    if found_driver is None:
        handler.json({'error': 'bad_driver'}, 400)
    else:
        driver_steps = yield found_driver.get_steps()
        if step_index >= len(driver_steps):
            handler.json({'error': 'bad_step'}, 400)
        else:
            if step_index < 0 or driver_steps[step_index].validate(field_values):
                result = yield found_driver.validate_field_values(step_index, field_values)
                handler.json(result.serialize())
            else:
                handler.json({
                    'errors': ['Some fields are not filled.'],
                    'new_step_index': step_index,
                    'option_choices': None
                })


@auth_only
@coroutine
def create_host(handler):
    try:
        body = json.loads(handler.request.body)
        host_name = str(body['host_name'])
        driver = str(body['driver_id'])
        field_values = dict(body['field_values'])
    except:
        handler.json({'error' 'bad_body'}, 400)
    else:
        handler.config.deploy_handler.create_host(host_name, driver, field_values)
