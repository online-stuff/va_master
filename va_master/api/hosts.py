from .login import auth_only
import tornado.gen
from tornado.gen import Return
import json
import panels



def get_paths():
    paths = {
        'get' : {
            'hosts/reset' : {'function' : reset_hosts, 'args' : []},
            'drivers' : {'function' : list_drivers, 'args' : []},
            'hosts/get_trigger_functions': {'function' : get_hosts_triggers, 'args' : ['hostname']},
            'hosts/get_host_billing' : {'function' : get_host_billing, 'args' : ['hostname']},
            'hosts' : {'function' : list_hosts, 'args' : []},

        },
        'post' : {
            'hosts' : {'function' : list_hosts, 'args' : []},
            'hosts/info' : {'function' : get_host_info, 'args' : ['required_hosts', 'get_billing', 'get_instances']},
            'hosts/new/validate_fields' : {'function' : validate_newhost_fields, 'args' : ['handler']},
            'hosts/delete' : {'function' : delete_host, 'args' : ['hostname']},
            'hosts/add_host' : {'function' : add_host, 'args' : ['field_values', 'driver_name']},
            'hosts/generic_add_instance' : {'function' : add_generic_instance, 'args' : []},
        }
    }
    return paths


@tornado.gen.coroutine
def add_host(deploy_handler):
    host_field_values = {"username": "user", "sizes": [], "images": [], "hostname": "sample_host", "instances": [], "driver_name": "generic_driver", "defaults": {}, "sec_groups": [], "password": "pass", "ip_address": "127.0.0.1", "networks": []}
    host_field_values.update(handler.data['field_values'])

    driver = yield deploy_handler.get_driver_by_id(handler.data['driver_name'])
    driver.field_values = host_field_values

    yield deploy_handler.create_host(driver)
    if host_field_values['driver_name'] == 'generic_driver' : 
        deploy_handler.datastore.insert(host_field_values['hostname'], {"instances" : []})


    raise tornado.gen.Return(True)


@tornado.gen.coroutine
def add_generic_instance(deploy_handler):
    base_instance = {"hostname" : "", "ip" : "", "local_gb" : 0, "memory_mb" : 0, "status" : "n/a" }
    base_instance.update(handler.data['instance'])

    instances = yield deploy_handler.datastore.get(handler.data['hostname'])
    instances['instances'].append(base_instance)
    yield deploy_handler.datastore.insert(handler.data['hostname'], instances)

@tornado.gen.coroutine
def get_host_billing(deploy_handler):
    host, driver = yield deploy_handler.get_host_and_driver(hostname)
    result = yield driver.get_host_billing(host)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_hosts_triggers(deploy_handler, hostname):
    host, driver = yield deploy_handler.get_host_and_driver(hostname)
    result = yield driver.get_driver_trigger_functions()
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def list_hosts(deploy_handler):
    hosts = yield deploy_handler.list_hosts()
    hidden_instances = yield deploy_handler.datastore.get('hidden_instances')
    for host in hosts: 
        driver = yield deploy_handler.get_driver_by_id(host['driver_name'])
        host['instances'] = yield driver.get_instances(host)
        if hidden_instances: 
            host['instances'] = [x for x in host['instances'] if x['hostname'] not in hidden_instances]

    raise tornado.gen.Return({'hosts': hosts})


@tornado.gen.coroutine
def reset_hosts(deploy_handler):
    yield deploy_handler.datastore.insert('hosts', [])


@tornado.gen.coroutine
def delete_host(deploy_handler, hostname):
    hosts = yield deploy_handler.datastore.get('hosts')
    hosts = [x for x in hosts if not x['hostname'] == hostname]
    yield deploy_handler.datastore.insert('hosts', hosts)


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
def validate_newhost_fields(deploy_handler, handler):
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
                print 'Result is : ', result, ' with index : ', result.new_step_index
                if result.new_step_index == -1:
                    deploy_handler.create_host(found_driver)
                raise tornado.gen.Return(result.serialize())
            else:
                result = {
                    'errors': ['Some fields are not filled.'],
                    'new_step_index': step_index,
                    'option_choices': None
                }
            raise tornado.gen.Return(result)



@tornado.gen.coroutine
def get_host_info(deploy_handler, get_billing = True, get_instances = True, required_hosts = []):
    store = deploy_handler.datastore
    hidden_instances = yield store.get('hidden_instances')

    hosts = yield deploy_handler.list_hosts()

    if required_hosts: 
        hosts = [host for host in hosts if host['hostname'] in required_hosts]

    host_drivers = yield [deploy_handler.get_driver_by_id(x['driver_name']) for x in hosts]
    hosts_data = [x[0].get_host_data(host = x[1], get_instances = get_instances, get_billing = get_billing) for x in zip(host_drivers, hosts)]
    hosts_info = yield hosts_data
    
    if hidden_instances: 
        for host in hosts_info:
            host['instances'] = [x for x in host['instances'] if x['hostname'] not in hidden_instances]

    for info in zip(hosts_info, hosts): 
        info[0]['hostname'] = info[1]['hostname']

    raise tornado.gen.Return(hosts_info)

