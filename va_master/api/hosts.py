from .login import auth_only
import tornado.gen
from tornado.gen import Return
import json
import panels



def get_paths():
    paths = {
        'get' : {
            'hosts' : list_hosts, 
            'hosts/reset' : reset_hosts, 
            'drivers' : list_drivers, 

        },
        'post' : {
            'hosts/info' : get_host_info, 
            'hosts/new/validate_fields' : validate_newhost_fields, 
            'hosts/delete' : delete_host, 
        }
    }
    return paths

##@auth_only(user_allowed = True)
@tornado.gen.coroutine
def list_hosts(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    for host in hosts: 
        driver = yield handler.config.deploy_handler.get_driver_by_id(host['driver_name'])
        host['instances'] = yield driver.get_instances(host)
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
                try: 
                    result = yield found_driver.validate_field_values(step_index, field_values)
                except tornado.gen.Return: 
                    raise
                except Exception as e:
                    raise tornado.gen.Return({'success' : False, 'message' : 'Could not validate field values. Error was : ' + e.message, 'data' : {}})
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

    hosts_data = [x[0].get_host_data(x[1]) for x in zip(host_drivers, hosts)]
    hosts_info = yield hosts_data
    
    for info in zip(hosts_info, hosts): 
        info[0]['hostname'] = info[1]['hostname']

    raise tornado.gen.Return(hosts_info)

