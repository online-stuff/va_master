import tornado.gen
import clc
import salt.client
from tornado.concurrent import run_on_executor
evo_target = 'evo-master'

def get_paths():
    return {
        'get' : {
            'evo/api_call' : clc_api_call,
            'evo/get_server': get_server_data,
            'evo/get_users' : get_users,
            'evo/get_server_auth' : get_auth,
        },
        'post' : {
            'evo/api_call' : clc_api_call,
            'evo/set_server_stats' : set_server_stats,
            'evo/evo_manager_api' : evo_manager_api,
        },
        'delete' : {
            'evo/delete_ts' : delete_server,
        },
        'user_allowed' : ['evo/get_server_auth'],
    }


@tornado.gen.coroutine
def evo_manager_api(handler):
    cl = salt.client.LocalClient()
    salt_args = [handler.data['function']]
    if handler.data.get('args'): 
        for x in handler.data.get('args'): salt_args.append(x)

    result = cl.cmd(evo_target, handler.data['function'], handler.data['args'])['evo-master']

    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_users(handler):
    cl = salt.client.LocalClient()
    users = cl.cmd(evo_target, 'evo_manager.get_users')
    raise tornado.gen.Return(users)


@tornado.gen.coroutine
def get_terminals(handler):
    cl = salt.client.LocalClient()
    terminals = cl.cmd(evo_target, 'evo_manager.get_terminals')
    raise tornado.gen.Return(terminals)  

@tornado.gen.coroutine
def delete_server(handler):
    store = handler.config.deploy_handler.datastore

    hosts = yield store.get('hosts')
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]
    driver = yield handler.config.deploy_handler.get_driver_by_id(host['driver_name'])
   
    try: 
        server = yield driver.delete_server(host, handler.data['server_id'])
    except: 
        import traceback
        traceback.print_exc()
    raise tornado.gen.Return(server)
   


@tornado.gen.coroutine
def get_server_data(handler):
    store = handler.config.deploy_handler.datastore

    hosts = yield store.get('hosts')
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]
    driver = yield handler.config.deploy_handler.get_driver_by_id(host['driver_name'])
   
    server = yield driver.get_server_data(host, handler.data['server_name'])
    raise tornado.gen.Return(server)


@tornado.gen.coroutine
def get_auth(handler):
    from salt.client import LocalClient 
    cl = LocalClient()
    try:
        user_auth = cl.cmd('evo-master', 'evo_utils.get_user_auth', [handler.data['user_email']])['evo-master']
        user_auth['ip'] = '206.142.244.70'
        print ('Got user auth : ', user_auth)
    except: 
        import traceback
        traceback.print_exc()
    raise tornado.gen.Return(user_auth)


@tornado.gen.coroutine
def clc_api_call(handler):
    store = handler.config.deploy_handler.datastore

    hosts = yield store.get('hosts')
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]
    driver = yield handler.config.deploy_handler.get_driver_by_id(host['driver_name'])

    result = yield driver.api_call(host, handler.data)
    print ('clc_api_call returned ', result)
    raise tornado.gen.Return(result)


@tornado.gen.coroutine
def set_server_stats(handler):
    store = handler.config.deploy_handler.datastore

    hosts = yield store.get('hosts')
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]
    driver = yield handler.config.deploy_handler.get_driver_by_id(host['driver_name'])

    result = yield driver.server_set_stats(host = host, instance_name = handler.data['server_id'], cpu = handler.data['cpu'], memory = handler.data['memory'], add = handler.data.get('add', False))
    raise tornado.gen.Return(result)


@tornado.gen.coroutine
def allocate_terminal_server(handler):
    cl = salt.client.LocalClient()
    data = handler_data

    result = cl.cmd('evo_master', 'evo_manager.new_user', [data.username, data.email, data.password, data.nesho])
    raise tornado.gen.Return(result)

