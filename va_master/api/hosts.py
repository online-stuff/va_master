from .login import auth_only
import tornado.gen
from tornado.gen import Return
import json
import panels



def get_paths():
    paths = {
        'get' : {
            'providers/reset' : {'function' : reset_providers, 'args' : []},
            'drivers' : {'function' : list_drivers, 'args' : []},
            'providers/get_trigger_functions': {'function' : get_providers_triggers, 'args' : ['provider_name']},
            'providers/get_provider_billing' : {'function' : get_provider_billing, 'args' : ['provider_name']},
            'providers' : {'function' : list_providers, 'args' : []},

        },
        'post' : {
            'providers' : {'function' : list_providers, 'args' : []},
            'providers/info' : {'function' : get_provider_info, 'args' : ['required_providers', 'get_billing', 'get_servers', 'sort_by_location']},
            'providers/new/validate_fields' : {'function' : validate_new_provider_fields, 'args' : ['handler']},
            'providers/delete' : {'function' : delete_provider, 'args' : ['provider_name']},
            'providers/add_provider' : {'function' : add_provider, 'args' : ['field_values', 'driver_name']},
            'providers/generic_add_server' : {'function' : add_generic_server, 'args' : ['provider_name', 'server']},
        }
    }
    return paths


@tornado.gen.coroutine
def add_provider(deploy_handler, field_values, driver_name):
    provider_field_values = {"username": "user", "sizes": [], "images": [], "provider_name": "sample_provider", "servers": [], "driver_name": "generic_driver", "defaults": {}, "sec_groups": [], "password": "pass", "ip_address": "127.0.0.1", "networks": []}
    provider_field_values.update(field_values)

    driver = yield deploy_handler.get_driver_by_id(driver_name)
    driver.field_values = provider_field_values

    yield deploy_handler.create_provider(driver)
    if provider_field_values['driver_name'] == 'generic_driver' : 
        deploy_handler.datastore.insert(provider_field_values['provider_name'], {"servers" : []})


    raise tornado.gen.Return(True)


@tornado.gen.coroutine
def add_generic_server(deploy_handler, provider_name, server):
    base_server = {"hostname" : "", "ip" : "", "local_gb" : 0, "memory_mb" : 0, "status" : "n/a" }
    base_server.update(server)

    servers = yield deploy_handler.datastore.get(provider_name)
    servers['servers'].append(base_server)
    yield deploy_handler.datastore.insert(provider_name, servers)

@tornado.gen.coroutine
def get_provider_billing(deploy_handler):
    provider, driver = yield deploy_handler.get_provider_and_driver(provider_name)
    result = yield driver.get_provider_billing(provider)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_providers_triggers(deploy_handler, provider_name):
    provider, driver = yield deploy_handler.get_provider_and_driver(provider_name)
    result = yield driver.get_driver_trigger_functions()
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def list_providers(deploy_handler):
    providers = yield deploy_handler.list_providers()

    try:
        hidden_servers = yield deploy_handler.datastore.get('hidden_servers')
    except: 
        hidden_servers = []

    for provider in providers: 
        driver = yield deploy_handler.get_driver_by_id(provider['driver_name'])
        provider['servers'] = yield driver.get_servers(provider)
        if hidden_servers: 
            provider['servers'] = [x for x in provider['servers'] if x['hostname'] not in hidden_servers]

    raise tornado.gen.Return({'providers': providers})


@tornado.gen.coroutine
def reset_providers(deploy_handler):
    yield deploy_handler.datastore.insert('providers', [])


@tornado.gen.coroutine
def delete_provider(deploy_handler, provider_name):
    providers = yield deploy_handler.datastore.get('providers')
    providers = [x for x in providers if not x['provider_name'] == provider_name]
    yield deploy_handler.datastore.insert('providers', providers)


@tornado.gen.coroutine
def list_drivers(deploy_handler):
    drivers = yield deploy_handler.get_drivers()
    out = {'drivers': []}
    for driver in drivers:
        driver_id = yield driver.driver_id()
        name = yield driver.friendly_name()
        steps = yield driver.get_steps()
        steps = [x.serialize() for x in steps]
        out['drivers'].append({'id': driver_id,
            'friendly_name': name, 'steps': steps})
    raise tornado.gen.Return(out)

@tornado.gen.coroutine
def validate_new_provider_fields(deploy_handler, handler):
    ok = True
    try:
        body = json.loads(handler.request.body)
        driver_id = str(body['driver_id'])
        field_values = dict(body['field_values'])
        step_index = int(body['step_index'])

    except Exception as e:
        raise tornado.gen.Return({'error': 'bad_body', 'msg' : e}, 400)

    found_driver = yield deploy_handler.get_driver_by_id(driver_id)

    if found_driver is None:
        raise tornado.gen.Return({'error': 'bad_driver'}, 400)
    else:
        try:
            driver_steps = yield found_driver.get_steps()
        except: 
            import traceback
            traceback.print_exc()
        if step_index >= len(driver_steps):
            raise tornado.gen.Return({'error': 'bad_step'}, 400)
        else:
            if step_index < 0 or driver_steps[step_index].validate(field_values):
                result = yield found_driver.validate_field_values(step_index, field_values)
                if result.new_step_index == -1:
                    deploy_handler.create_provider(found_driver)
                raise tornado.gen.Return(result.serialize())
            else:
                result = {
                    'errors': ['Some fields are not filled.'],
                    'new_step_index': step_index,
                    'option_choices': None
                }
            raise tornado.gen.Return(result)



@tornado.gen.coroutine
def get_provider_info(deploy_handler, get_billing = True, get_servers = True, required_providers = [], sort_by_location = False):
    store = deploy_handler.datastore
    try:
        hidden_servers = yield store.get('hidden_servers')
    except: 
        hidden_servers = []

    providers = yield deploy_handler.list_providers()

    if required_providers: 
        providers = [provider for provider in providers if provider['provider_name'] in required_providers]

    provider_drivers = yield [deploy_handler.get_driver_by_id(x['driver_name']) for x in providers]
    providers_data = [x[0].get_provider_data(provider = x[1], get_servers = get_servers, get_billing = get_billing) for x in zip(provider_drivers, providers)]
    providers_info = yield providers_data
    
    if hidden_servers: 
        for provider in providers_info:
            provider['servers'] = [x for x in provider['servers'] if x['hostname'] not in hidden_servers]

    for info in zip(providers_info, providers): 
        info[0]['provider_name'] = info[1]['provider_name']
        info[0]['location'] = info[1]['location']

    if sort_by_location: 
        #Convert to {"location" : [list, of, providers], "location2" : [list, of, other, providers]}
        providers_info = {l : [x for x in providers_info if x['location'] == l] for l in [x['location'] for x in providers_info]}

    raise tornado.gen.Return(providers_info)

