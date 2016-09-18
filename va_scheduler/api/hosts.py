from .login import auth_only
from ..drivers.base import HostStepInput, HostStepOutput
import tornado.gen
import json

@auth_only
@tornado.gen.coroutine
def list_hosts(handler):
    yield tornado.gen.sleep(1)
    handler.json({'hi': True})

@auth_only
@tornado.gen.coroutine
def list_drivers(handler):
    drivers = handler.config.host_drivers
    out = {'drivers': []}
    for driver in drivers:
        driver_id = yield driver.driver_id()
        name = yield driver.friendly_name()
        steps = yield driver.new_host_step_descriptions()
        out['drivers'].append({'id': driver_id,
            'friendly_name': name, 'steps': steps})
    handler.json(out)

@auth_only
@tornado.gen.coroutine
def new_host_step(handler):
    ok = True
    try:
        body = json.loads(handler.request.body)
        field_values = body['field_values']
        state = body['state']
        driver_id = body['driver_id']
    except:
        handler.json({'error': 'bad_body'}, 400)
        ok = False
    if ok:
        found_driver = None
        for allowed_driver in handler.config.host_drivers:
            if allowed_driver.driver_id() == driver_id:
                found_driver = allowed_driver
                break
        if found_driver is None:
            handler.json({'error': 'driver_not_found'})
        else:
            client_input = HostStepInput(field_values, state)
            output = driver_base.new_host_step(client_input)
            client.json(output.serialize())
