import json

import salt.client
import tornado.gen
import login, apps

from login import auth_only, create_user_api


def get_paths():
    paths = {
        'get' : {
            'panels' : {'function' : get_panels, 'args' : ['handler', 'dash_user']}, 
            'panels/get_panel' : {'function' : get_panel_for_user, 'args' : ['handler', 'server_name', 'panel', 'provider', 'handler', 'args', 'dash_user']},
            'panels/users' : {'function' : get_users, 'args' : ['handler', 'users_type']},
            'panels/get_all_functions' : {'function' : get_all_functions, 'args' : ['handler']},
            'panels/get_all_function_groups' : {'function' : get_all_function_groups, 'args' : ['datastore_handler']},
        },
        'post' : {
            'panels/add_user_functions' : {'function' : add_user_functions, 'args' : ['datastore_handler', 'user', 'functions']},
            'panels/create_user_group' : {'function' : create_user_group, 'args' : ['datastore_handler', 'group_name', 'functions']},
            'panels/create_user_with_group' : {'function' : create_user_with_group, 'args' : ['handler', 'user', 'password', 'user_type', 'functions', 'groups']},
            'panels/delete_user' : {'function' : delete_user, 'args' : ['datastore_handler', 'user']}, 
            'panels/update_user' : {'function' : update_user, 'args' : ['datastore_handler', 'user', 'functions', 'groups', 'password']}, 

            'panels/get_panel' : {'function' : get_panel_for_user, 'args' : ['server_name', 'panel', 'provider', 'handler', 'args', 'dash_user']},
            'panels/reset_panels': {'function' : reset_panels, 'args' : []}, #JUST FOR TESTING
            'panels/new_panel' : {'function' : new_panel, 'args' : ['datastore_handler', 'panel_name', 'role']},
            'panels/action' : {'function' : panel_action, 'args' : ['handler', 'server_name', 'action', 'args', 'kwargs', 'module', 'dash_user']}, #must have server_name and action in data, 'args' : []}, ex: panels/action server_name=nino_dir action=list_users
            'panels/chart_data' : {'function' : get_chart_data, 'args' : ['server_name', 'args']},
            'panels/serve_file' : {'function' : salt_serve_file, 'args' : ['handler', 'server_name', 'action', 'args', 'kwargs', 'module']},
            'panels/serve_file_from_url' : {'function' : url_serve_file, 'args' : ['handler', 'server_name', 'url_function', 'module', 'args', 'kwargs']},
        }
    }
    return paths

@tornado.gen.coroutine
def reset_panels(deploy_handler): 
    yield deploy_handler.reset_panels()

@tornado.gen.coroutine
def new_panel(datastore_handler, panel_name, role):
    yield datastore_handler.add_panel(panel_name, role)


@tornado.gen.coroutine
def list_panels(datastore_handler, dash_user):
    panels = yield datastore_handler.get_panels(dash_user['type'])

    raise tornado.gen.Return(panels)

@tornado.gen.coroutine
def panel_action_execute(handler, server_name, action, args = [], dash_user = '', kwargs = {}, module = None, timeout = 30):
    datastore_handler = handler.datastore_handler
    if dash_user.get('username'):
        user_funcs = yield datastore_handler.get_user_salt_functions(dash_user['username'])
        if action not in user_funcs and dash_user['type'] != 'admin':
            print ('Function not supported')
            #TODO actually not allow user to do anything. This is just for testing atm. 
        
    server_info = yield apps.get_app_info(server_name)
    state = server_info['role']

    state = yield datastore_handler.get_state(name = state)
    if not state: state = {'module' : 'openvpn'}

    if not module:
        module = state['module']

    cl = salt.client.LocalClient()
    print ('Calling salt module ', module + '.' + action, ' on ', server_name, ' with args : ', args, ' and kwargs : ', kwargs)
    result = cl.cmd(server_name, module + '.' + action , args, kwarg = kwargs, timeout = timeout)
    result = result.get(server_name)

    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def salt_serve_file(handler, server_name, action, args = [], dash_user = '', kwargs = {}, module = None):
    datastore_handler = handler.datastore_handler
    server_info = yield apps.get_app_info(server_name)
    state = server_info['role']

    states = yield datastore_handler.get_states()
    state = [x for x in states if x['name'] == state] or [{'module' : 'openvpn'}]
    state = state[0]

    if not module:
        module = state['module']

    yield handler.serve_file('test', salt_source = {"tgt" : server_name, "fun" : module + '.' + action, "arg" :  args})
    raise tornado.gen.Return({"data_type" : "file"})


#This is just temporary - trying to get backup download working properly. 
@tornado.gen.coroutine
def salt_serve_file_get(handler, server_name, action, hostname, backupnumber, share, path, module = None):
    datastore_handler = handler.datastore_handler
    server_info = yield apps.get_app_info(server_name)
    state = server_info['role']

    states = yield datastore_handler.get_states()
    state = [x for x in states if x['name'] == state] or [{'module' : 'openvpn'}]
    state = state[0]

    if not module:
        module = state['module']

    kwargs = {
        'hostname' : hostname, 
        'backupnumber' : backupnumber, 
        'share' : share, 
        'path' : path, 
        'range_from' : 0,
    }

    yield handler.serve_file('test', salt_source = {"tgt" : server_name, "fun" : module + '.' + action, "kwarg" : kwargs})
    raise tornado.gen.Return({"data_type" : "file"})


@tornado.gen.coroutine
def url_serve_file(handler, server_name, url_function, module = None, args = [], kwargs = {}):
    datastore_handler = handler.datastore_handler
    server_info = yield apps.get_app_info(server_name)
    state = server_info['role']

    states = yield datastore_handler.get_states()
    state = [x for x in states if x['name'] == state] or [{'module' : 'openvpn'}]
    state = state[0]

    if not module:
        module = state['module']

    cl = salt.client.LocalClient()
    url = cl.cmd(server_name, module + '.' + url_function, arg = args, kwarg = kwargs).get(server_name)

    yield handler.serve_file('test', url_source = url)
    raise tornado.gen.Return({"data_type" : "file"})

@tornado.gen.coroutine
def get_chart_data(server_name, args = ['va-directory', 'Ping']):
    cl = salt.client.LocalClient()

    result = cl.cmd(server, 'monitoring_stats.parse' , args)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def panel_action(handler, actions_list = [], server_name = '', action = '', args = [], kwargs = {}, module = None, dash_user = {}):
    if not actions_list: 
        actions_list = [{"server_name" : server_name, "action" : action, "args" : args, 'kwargs' : {}, 'module' : module}]

    servers = [x['server_name'] for x in actions_list]
    results = {x : None for x in servers}
    for action in actions_list: 
        server_result = yield panel_action_execute(handler, action['server_name'], action['action'], action['args'], action['kwargs'], action['module'])
        results[action['server_name']] = server_result

    if len(results.keys()) == 1: 
        results = results[results.keys()[0]]
    raise tornado.gen.Return(results)


@tornado.gen.coroutine
def get_panels(handler, dash_user):
    datastore_handler = handler.datastore_handler
    panels = yield list_panels(datastore_handler, dash_user)
    raise tornado.gen.Return(panels)

@tornado.gen.coroutine
def get_panel_for_user(handler, panel, server_name, dash_user, args = [], provider = None, kwargs = {}):

    user_panels = yield list_panels(handler.datastore_handler, dash_user)
    server_info = yield apps.get_app_info(server_name)
    state = server_info['role']

    #This is usually for get requests. Any arguments in the url that are not arguments of this function are assumed to be keyword arguments for salt.
    #TODO Also this is pretty shabby, and I need to find a better way to make GET salt requests work. 
    if not args: 
        ignored_kwargs = ['datastore', 'handler', 'datastore_handler', 'deploy_handler', 'panel', 'instance_name', 'dash_user', 'method', 'server_name', 'path']
        kwargs = {x : handler.data[x] for x in handler.data if x not in ignored_kwargs}
    else: 
        kwargs = {}

    state = filter(lambda x: x['name'] == state, user_panels)[0]
    if server_name in state['servers']:
        action = 'get_panel'
        if type(args) != list and args: 
            args = [args]
        args = [panel] + args
        panel  = yield panel_action_execute(handler, server_name, action, args, dash_user, kwargs = kwargs)
        raise tornado.gen.Return(panel)
    else: 
        raise Exception("Requested salt call on " + server_name + " but that server name is not in the list of servers for " + state['name'] + " : " + str(state['servers']))

@tornado.gen.coroutine
def get_users(handler, user_type = 'users'):
    datastore_handler = handler.datastore_handler
    users = yield datastore_handler.get_users(user_type)
    result = []
    for u in users: 
        u_all_functions = yield datastore_handler.get_user_functions(u)
        print ('u_all_functions are : ', u_all_functions, ' for user : ', u)
        u_groups = [x.get('func_name') for x in u_all_functions if x.get('func_type', '') == 'function_group']
        u_functions = [x.get('func_path') for x in u_all_functions if x.get('func_path')]
        print ('Functinos are : ', u_functions)
        user_data = {
            'user' : u, 
            'functions' : u_functions, 
            'groups' : u_groups
        }
        result.append(user_data)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_all_functions(handler):
    functions = {m : handler.paths[m].keys() for m in ['post', 'get']}
    salt_functions = {} #TODO salt functinos should look like {backuppc:[list, of, functions], owncloud : [list, of, ofunctions]}

    functions.update(salt_functions)

    functions = [
            { 'label' : f, 'options' : [{'label' : i, 'value' : i} for i in functions[f]] }
    for f in functions]

    raise tornado.gen.Return(functions)


@tornado.gen.coroutine
def get_all_function_groups(datastore_handler):
    groups = yield datastore_handler.get_user_groups()
    for g in groups:
        g['functions'] = [x.get('func_path') for x in g['functions']]
    raise tornado.gen.Return(groups)

@tornado.gen.coroutine
def update_user(datastore_handler, user, functions = [], groups = [], password = ''):
    if password: 
        yield datastore_handler.update_user(user, password)
    print ('Groups are : ', groups, ' and funcs : ', functions)
    group_funcs = [datastore_handler.get_user_group(x) for x in groups]
    group_funcs = yield group_funcs
    [x.update({'func_type' : 'function_group'}) for x in group_funcs]
    print ('Funcs are : ', group_funcs)
    functions += group_funcs
    print ('Updating ', user, ' with ', functions)

    yield datastore_handler.set_user_functions(user, functions)


#functions should have format [{"func_path" : "/panels/something", "func_type" : "salt"}, ...]
@tornado.gen.coroutine
def add_user_functions(datastore_handler, user, functions):
    yield datastore_handler.add_user_functions(user, functions)
    
@tornado.gen.coroutine
def create_user_group(datastore_handler, group_name, functions):
    yield datastore_handler.create_user_group(group_name, functions)

@tornado.gen.coroutine
def create_user_with_group(handler, user, password, user_type, functions = [], groups = []):
    datastore_handler = handler.datastore_handler
    yield create_user_api(handler, user, password, user_type)
    all_groups = yield datastore_handler.get_user_groups()
    for g in groups: 
        required_group = [x for x in all_groups if x.get('func_name', '') == g]
        functions += required_group
    print ('Functions are : ', functions)
    yield add_user_functions(datastore_handler, user, functions)

@tornado.gen.coroutine
def delete_user(datastore_handler, user):
    yield datastore_handler.delete_user(user)