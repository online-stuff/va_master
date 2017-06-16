from .login import auth_only
import tornado.gen
from tornado.gen import Return
import json
import panels



def get_paths():
    paths = {
        'get' : {
            'hosts/reset' : reset_hosts, 
            'drivers' : list_drivers, 
            'hosts/get_trigger_functions': get_hosts_triggers,
            'hosts/get_host_billing' : get_host_billing, 
            'hosts' : list_hosts, 

        },
        'post' : {
            'hosts' : list_hosts, 
            'hosts/info' : get_host_info, 
            'hosts/new/validate_fields' : validate_newhost_fields, 
            'hosts/delete' : delete_host, 
            'hosts/add_host' : add_host,
            'hosts/generic_add_instance' : add_generic_instance,
        }
    }
    return paths


@tornado.gen.coroutine
def add_host(handler):
    host_field_values = {"username": "user", "sizes": [], "images": [], "hostname": "sample_host", "instances": [], "driver_name": "generic_driver", "defaults": {}, "sec_groups": [], "password": "pass", "ip_address": "127.0.0.1", "networks": []}
    host_field_values.update(handler.data['field_values'])

    driver = yield handler.config.deploy_handler.get_driver_by_id(handler.data['driver_name'])
    driver.field_values = host_field_values

    yield handler.config.deploy_handler.create_host(driver)
    if host_field_values['driver_name'] == 'generic_driver' : 
        handler.config.deploy_handler.datastore.insert(host_field_values['hostname'], {"instances" : []})


    raise tornado.gen.Return(True)


@tornado.gen.coroutine
def add_generic_instance(handler):
    base_instance = {"hostname" : "", "ipv4" : "", "local_gb" : 0, "memory_mb" : 0, "status" : "n/a" }
    base_instance.update(handler.data['instance'])

    instances = yield handler.config.deploy_handler.datastore.get(handler.data['hostname'])
    instances['instances'].append(base_instance)
    yield handler.config.deploy_handler.datastore.insert(handler.data['hostname'], instances)

@tornado.gen.coroutine
def get_host_billing(handler):
    host, driver = yield handler.config.deploy_handler.get_host_and_driver(handler.data['hostname'])
    result = yield driver.get_host_billing(host)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_hosts_triggers(handler):
    host, driver = yield handler.config.deploy_handler.get_host_and_driver(handler.data['hostname'])
    result = yield driver.get_driver_trigger_functions()
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def list_hosts(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    for host in hosts: 
        driver = yield handler.config.deploy_handler.get_driver_by_id(host['driver_name'])
        host['instances'] = yield driver.get_instances(host)
        if handler.data.get('filter_instances'): 
            host['instances'] = [x for x in host['instances'] if x['hostname'] in handler.data.get('filter_instances')]

    raise tornado.gen.Return({'hosts': hosts})


@tornado.gen.coroutine
def reset_hosts(handler):
    yield handler.config.deploy_handler.datastore.insert('hosts', [])


@tornado.gen.coroutine
def delete_host(handler):
    host = handler.data['hostname']
    hosts = yield handler.config.deploy_handler.datastore.get('hosts')
    hosts = [x for x in hosts if not x['hostname'] == host]
    yield handler.config.deploy_handler.datastore.insert('hosts', hosts)


#Doesn't work with API right now because of some auth issues. For some reason, if auth is on, it thinks the user is not an admin and fucks everything up. 
#Just a note for future reference, this needs to be fixed soon. 
##@auth_only
@tornado.gen.coroutine
def list_drivers(handler):
    drivers = yield handler.config.deploy_handler.get_drivers()
    out = {'drivers': []}
    for driver in drivers:
        driver_id = yield driver.driver_id()
        name = yield driver.friendly_name()
        steps = yield driver.get_steps()
        steps = [x.serialize() for x in steps]
        out['drivers'].append({'id': driver_id,
            'friendly_name': name, 'steps': steps})
#    raise Exception(json.dumps(out))
    raise tornado.gen.Return(out)

#@auth_only
@tornado.gen.coroutine
def validate_newhost_fields(handler):
    ok = True
    try:
        body = json.loads(handler.request.body)
        driver_id = str(body['driver_id'])
        field_values = dict(body['field_values'])
        step_index = int(body['step_index'])

    except Exception as e:
        raise tornado.gen.Return({'error': 'bad_body', 'msg' : e}, 400)

    found_driver = yield handler.config.deploy_handler.get_driver_by_id(driver_id)

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
                print 'Result is : ', result, ' with index : ', result.new_step_index
                if result.new_step_index == -1:
                    handler.config.deploy_handler.create_host(found_driver)
                raise tornado.gen.Return(result.serialize())
            else:
                result = {
                    'errors': ['Some fields are not filled.'],
                    'new_step_index': step_index,
                    'option_choices': None
                }
            raise tornado.gen.Return(result)


#@auth_only
@tornado.gen.coroutine
def create_host(handler):
    try:
        body = json.loads(handler.request.body)
        host_name = str(body['host_name'])
        driver = str(body['driver_id'])
        field_values = dict(body['field_values'])
    except:
        raise tornado.gen.Return({'error' 'bad_body'}, 400)
    else:
        handler.config.deploy_handler.create_host(host_name, driver, field_values)


@tornado.gen.coroutine
def get_host_info(handler):
    data = handler.data
    deploy_handler = handler.config.deploy_handler
    store = deploy_handler.datastore

    required_hosts = data.get('hosts')
    hosts = yield handler.config.deploy_handler.list_hosts()

    if required_hosts: 
        hosts = [host for host in hosts if host['hostname'] in required_hosts]

    host_drivers = yield [deploy_handler.get_driver_by_id(x['driver_name']) for x in hosts]
    hosts_data = [x[0].get_host_data(host = x[1], get_instances = data.get('get_instances', True), get_billing = data.get('get_billing', True)) for x in zip(host_drivers, hosts)]
    hosts_info = yield hosts_data
    
    if data.get('filter_instances'): 
        for host in hosts_info:
            host['instances'] = [x for x in host['instances'] if x['hostname'] in data.get('filter_instances')]

    for info in zip(hosts_info, hosts): 
        info[0]['hostname'] = info[1]['hostname']

    raise tornado.gen.Return(hosts_info)

