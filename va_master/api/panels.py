import json

import salt.client
import tornado.gen
import login, apps

from login import auth_only

def get_paths():
    paths = {
        'get' : {
            'panels' : {'function' : get_panels, 'args' : ['handler']}, 
            'panels/get_panel' : {'function' : get_panel_for_user, 'args' : ['instance_name', 'panel', 'host', 'handler', 'args', 'dash_user']},
            'panels/ts_data' : {'function' : get_ts_data, 'args' : []},  
        },
        'post' : {
            'panels/get_panel' : {'function' : get_panel_for_user, 'args' : ['instance_name', 'panel', 'host', 'handler', 'args', 'dash_user']},
            'panels/reset_panels': {'function' : reset_panels, 'args' : []}, #JUST FOR TESTING
            'panels/new_panel' : {'function' : new_panel, 'args' : ['panel_name', 'role']},
            'panels/action' : {'function' : panel_action, 'args' : ['instance_name', 'action', 'args', 'kwargs', 'module', 'dash_user']}, #must have instance_name and action in data, 'args' : []}, ex: panels/action instance_name=nino_dir action=list_users
            'panels/chart_data' : {'function' : get_chart_data, 'args' : ['instance_name', 'args']},
            'panels/serve_file' : {'function' : salt_serve_file, 'args' : ['instance_name', 'action', 'args', 'kwargs', 'module']},
        }
    }
    return paths

@tornado.gen.coroutine
def reset_panels(deploy_handler): 
    yield deploy_handler.reset_panels()

@tornado.gen.coroutine
def new_panel(deploy_handler, panel_name, role):
    states = yield deploy_handler.get_states_data()
    panel = {'panel_name' : panel_name, 'role' : role}
    panel.update([x for x in states if x['name'] == role][0]['panels'])
    yield deploy_handler.store_panel(panel)


@tornado.gen.coroutine
def list_panels(deploy_handler, handler): 
    user_group = yield login.get_user_type(handler)

    panels = yield deploy_handler.datastore.get('panels')
    panels = panels[user_group]

    raise tornado.gen.Return(panels)

@tornado.gen.coroutine
def panel_action_execute(deploy_handler, instance_name, action, args = [], dash_user = '', kwargs = {}, module = None, timeout = 30):
    try:
        print ('dash user is : ', dash_user)
        user_funcs = yield deploy_handler.get_user_salt_functions(dash_user['username'])
        if action not in user_funcs and dash_user['type'] != 'admin':
            print ('Function not supported')
            #TODO actually not allow user to do anything. This is just for testing atm. 
            

        print ('INstance name is : ', instance_name)
        instance_info = yield apps.get_app_info(deploy_handler, instance_name)
        state = instance_info['role']

        states = yield deploy_handler.get_states()
        state = [x for x in states if x['name'] == state] or [{'module' : 'openvpn'}]
        state = state[0]
        
        if not module: 
            module = state['module']

        cl = salt.client.LocalClient()
        print ('Calling salt module ', module + '.' + action, ' on ', instance_name, ' with args : ', args, ' and kwargs : ', kwargs)
        result = cl.cmd(instance_name, module + '.' + action , args, kwargs = kwargs, timeout = timeout)
        result = result.get(instance_name)
    except: 
        import traceback 
        traceback.print_exc()
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def salt_serve_file(deploy_handler, instance_name, action, args = [], kwargs = {}, module = None):

    instance_info = yield apps.get_app_info(deploy_handler, instance_name)
    state = instance_info['role']
    states = yield deploy_handler.get_states()
    state = [x for x in states if x['name'] == state] or [{'module' : 'openvpn'}]
    state = state[0]
    if not module: 
        module = state['module']

    action = module + '.' + action

    cl = salt.client.LocalClient()
    print ('Calilng serve on ', instance, ' with action ', action, ' with args : ', args, ' and kwargs : ', kwargs)
    result = cl.cmd(instance, action, args, kwargs = kwargs)
    result = result['va-backup']
    print ('Result is : ', result)
    path_to_file = '/tmp/some_salt_file'

    with open(path_to_file, 'w') as f: 
        f.write(result)

    yield handler.serve_file(path_to_file)

@tornado.gen.coroutine
def get_ts_data(deploy_handler):
    cl = salt.client.LocalClient()

    result = cl.cmd('va-monitoring.evo.mk', 'monitoring.chart_data')
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_chart_data(deploy_handler, instance_name, args = ['va-directory', 'Ping']):
    cl = salt.client.LocalClient()

    result = cl.cmd(instance, 'monitoring_stats.parse' , args)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def panel_action(deploy_handler, actions_list = [], instance_name = '', action = '', args = [], kwargs = {}, module = None):
    if not actions_list: 
        actions_list = [{"instance_name" : instance_name, "action" : action, "args" : args, 'kwargs' : {}, 'module' : module}]

    instances = [x['instance_name'] for x in actions_list]
    results = {x : None for x in instances}
    for action in actions_list: 
        instance_result = yield panel_action_execute(deploy_handler, action['instance_name'], action['action'], action['args'], action['kwargs'], action['module'])
        results[action['instance_name']] = instance_result

    if len(results.keys()) == 1: 
        results = results[results.keys()[0]]
    raise tornado.gen.Return(results)


@tornado.gen.coroutine
def get_panels(deploy_handler, handler):
    panels = yield list_panels(deploy_handler, handler)
    raise tornado.gen.Return(panels)

@tornado.gen.coroutine
def get_panel_for_user(deploy_handler, handler, panel, instance_name, dash_user, args = [], host = None):

    user_panels = yield list_panels(deploy_handler, handler)
    instance_info = yield apps.get_app_info(deploy_handler, instance_name)
    state = instance_info['role']
    print ('args are : ', args, ' and from handler: ', handler.data.get('args'))

    state = filter(lambda x: x['name'] == state, user_panels)[0]
    if instance_name in state['instances']:
        action = 'get_panel'
        if type(args) != list and args: 
            args = [args]
        args = [panel] + args
        try: 
            print ('Getting panel. ')
            panel  = yield panel_action_execute(deploy_handler, instance_name, action, args, dash_user)
            print ('Panel is : ', panel)
        except: 
            import traceback
            traceback.print_exc()

#        panel = panel[instance_name]
        raise tornado.gen.Return(panel)
    else: 
        raise tornado.gen.Return(False)



