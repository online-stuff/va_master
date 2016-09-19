from .login import auth_only
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
        steps = yield driver.get_steps()
        steps = [x.serialize() for x in steps]
        out['drivers'].append({'id': driver_id,
            'friendly_name': name, 'steps': steps})
    handler.json(out)

@tornado.gen.coroutine
def get_driver_by_id(driver_id, handler):
    found_driver = None
    for allowed_driver in handler.config.host_drivers:
        allowed_id = yield allowed_driver.driver_id()
        if allowed_id == driver_id:
            found_driver = allowed_driver
            break
    raise tornado.gen.Return(found_driver)

@auth_only
@tornado.gen.coroutine
def validate_newhost_fields(handler):
    ok = True
    try:
        body = json.loads(handler.request.body)
        driver_id = str(body['driver_id'])
        field_values = dict(body['field_values'])
        step_index = int(body['step_index'])
    except:
        handler.json({'error': 'bad_body'}, 400)
        ok = False
    if ok:
        found_driver = yield get_driver_by_id(driver_id, handler)
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
