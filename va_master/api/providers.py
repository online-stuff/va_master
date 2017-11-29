from .login import auth_only
import tornado.gen
from tornado.gen import Return
import json
import panels



def get_paths():
    paths = {
        'get' : {
            'drivers' : {'function' : list_drivers, 'args' : ['drivers_handler']},
            'providers/get_trigger_functions': {'function' : get_providers_triggers, 'args' : ['provider_name']},
            'providers/get_provider_billing' : {'function' : get_provider_billing, 'args' : ['provider_name']},
            'providers' : {'function' : list_providers, 'args' : ['handler']},

        },
        'post' : {
            'providers' : {'function' : list_providers, 'args' : ['handler']},
            'providers/info' : {'function' : get_provider_info, 'args' : ['handler', 'dash_user', 'required_providers', 'get_billing', 'get_servers', 'sort_by_location']},
            'providers/new/validate_fields' : {'function' : validate_new_provider_fields, 'args' : ['handler', 'driver_id', 'field_values', 'step_index']},
            'providers/delete' : {'function' : delete_provider, 'args' : ['datastore_handler', 'provider_name']},
            'providers/add_provider' : {'function' : add_provider, 'args' : ['datastore_handler', 'field_values', 'driver_name']},
            'providers/generic_add_server' : {'function' : add_generic_server, 'args' : ['datastore_handler', 'provider_name', 'server']},
        }
    }
    return paths

#Utility function used internally in the API. 
@tornado.gen.coroutine
def get_provider_and_driver(handler, provider_name = 'va_standalone_servers'):
    provider = yield handler.datastore_handler.get_provider(provider_name = provider_name)
    driver = yield handler.drivers_handler.get_driver_by_id(provider['driver_name'])

    raise tornado.gen.Return((provider, driver))

@tornado.gen.coroutine
def add_provider(datastore_handler, field_values, driver_name):
    """Creates a provider with the specified field values. Most of the time not used directly, but can be used by external APIs. """
    provider_field_values = {"username": "user", "sizes": [], "images": [], "provider_name": "sample_provider", "servers": [], "driver_name": "generic_driver", "defaults": {}, "sec_groups": [], "password": "pass", "ip_address": "127.0.0.1", "networks": []}
    provider_field_values.update(field_values)

    yield datastore_handler.create_provider(provider_field_values)

    raise tornado.gen.Return(True)


@tornado.gen.coroutine
def add_generic_server(datastore_handler, provider_name, server):
    """Adds a server to the list of servers for the specified provider. """
    base_server = {"hostname" : "", "ip" : "", "local_gb" : 0, "memory_mb" : 0, "status" : "n/a" }
    base_server.update(server)

    yield datastore_handler.add_generic_server(provider_name, base_server)

@tornado.gen.coroutine
def get_provider_billing(handler, provider_name):
    """Returns billing data for the specified provider. """
    provider, driver = yield get_provider_and_driver(handler, provider_name)
    result = yield driver.get_provider_billing(provider)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_providers_triggers(handler, provider_name):
    """Gets a list of triggers for the specified provider. """
    provider, driver = yield get_provider_and_driver(handler, provider_name)
    result = yield driver.get_driver_trigger_functions()
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def list_providers(handler):
    """Gets a list of providers from the datastore. Adds the driver name to the list, and gets the status. Gets a list of servers for each provider and, if there are any hidden servers, they are removed from the list. """
    datastore_handler = handler.datastore_handler
    drivers_handler = handler.drivers_handler

    providers = yield datastore_handler.list_providers()
    hidden_servers = yield datastore_handler.get_hidden_servers()

    for provider in providers: 
        driver = yield drivers_handler.get_driver_by_id(provider['driver_name'])
        provider['servers'] = yield driver.get_servers(provider)
        
        provider_status = yield driver.get_provider_status(provider)
        provider['status'] = provider_status

        if hidden_servers: 
            provider['servers'] = [x for x in provider['servers'] if x['hostname'] not in hidden_servers]

    providers = [x for x in providers if x['provider_name']]

    raise tornado.gen.Return({'providers': providers})


@tornado.gen.coroutine
def delete_provider(datastore_handler, provider_name):
    """Deletes the provider with provider_name. """
    yield datastore_handler.delete_provider(provider_name)

@tornado.gen.coroutine
def list_drivers(drivers_handler):
    """Gets a list of drivers. """
    drivers = yield drivers_handler.get_drivers()
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
def validate_new_provider_fields(handler, driver_id, field_values, step_index):
    """Used when adding new providers. Makes sure all the fields are entered properly, and proceeds differently based on what driver is being used. """

    step_index = int(step_index)
    drivers_handler = handler.drivers_handler
    datastore_handler = handler.datastore_handler
    found_driver = yield drivers_handler.get_driver_by_id(driver_id)

    driver_steps = yield found_driver.get_steps()
    if step_index >= len(driver_steps) or step_index < -1:
        raise Exception('Step index was : ' + str(step_index) + ' but the number of steps is : ' + str(driver_steps))

    if step_index < 0 or driver_steps[step_index].validate(field_values):
        result = yield found_driver.validate_field_values(step_index, field_values)
        if result.new_step_index == -1:
            datastore_handler.create_provider(found_driver.field_values)
        raise tornado.gen.Return(result.serialize())
    else:
        result = {
            'errors': ['Some fields are not filled.'],
            'new_step_index': step_index,
            'option_choices': None
        }
    raise tornado.gen.Return(result)



@tornado.gen.coroutine
def get_provider_info(handler, dash_user, get_billing = True, get_servers = True, required_providers = [], sort_by_location = False):
    """
    Gets all info for all providers - servers and their usages, the provider usage, images, sizes, networks, security groups, billing info and all provider datastore data. 
    If get_billing is false, then the billing data will be empty. Same for get_servers. 
    If required_providers is set, the providers are filtered to only show the providers with a provider_name in that list. 
    If sort_by_location is true, then this sorts providers in a dictionary object where the keys are the locations of the providers. 
    """
    drivers_handler = handler.drivers_handler
    datastore_handler = handler.datastore_handler

    hidden_servers = yield datastore_handler.get_hidden_servers()
    providers = yield datastore_handler.list_providers()

    if required_providers: 
        providers = [provider for provider in providers if provider['provider_name'] in required_providers]

    provider_drivers = yield [drivers_handler.get_driver_by_id(x['driver_name']) for x in providers]
    providers_data = [x[0].get_provider_data(provider = x[1], get_servers = get_servers, get_billing = get_billing) for x in zip(provider_drivers, providers)]
    providers_info = yield providers_data
    
    states = yield panels.get_panels(handler, dash_user)

    for provider in providers_info:
        if hidden_servers: 
            provider['servers'] = [x for x in provider['servers'] if x['hostname'] not in hidden_servers]

        for server in provider['servers']:
            server_panel = [x for x in states if server.get('hostname', '') in x['servers']] or [{'icon' : 'fa-server'}]
            server['icon'] = server_panel[0]['icon']

    for info in zip(providers_info, providers): 
        info[0]['provider_name'] = info[1]['provider_name']
        info[0]['location'] = info[1]['location']

    providers_info = [x for x in providers_info if x['provider_name']]

    standalone_provider = yield datastore_handler.get_provider('va_standalone_servers')

    standalone_default_values = {'size' : ''}
    standalone_servers = standalone_provider['servers']
    for v in standalone_default_values: 
        [x.update({v : x.get(v, standalone_default_values[v])}) for x in standalone_servers]
    print ('Standalone_servers are : ', standalone_servers)
    standalone_locations = set([x.get('location', 'va-master') for x in standalone_servers])
    standalone_providers = [
        {
            "provider_name" : "", 
            "servers" : [x for x in standalone_servers if x.get('location', 'va-master') == l], 
            "location" : l,
        } for l in standalone_locations]
    providers_info += standalone_providers

    if sort_by_location: 
        #Convert to {"location" : [list, of, providers], "location2" : [list, of, other, providers]}


        providers_info = {l : 
            [x for x in providers_info if x.get('location', 'va-master') == l] for l in [x.get('location', 'va-master')
         for x in providers_info]}

    raise tornado.gen.Return(providers_info)

