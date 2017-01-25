import json

import salt.client
import tornado.gen
import login, apps

from login import auth_only

def get_paths():
    paths = {
        'get' : {
            'panels/reset_panels': reset_panels, #JUST FOR TESTING
            'panels/new_panel' : new_panel, #JUST FOR TESTING
            'panels' : get_panels, 
            'panels/get_panel' : get_panel_for_user, 
        },
        'post' : {
            'panels/action' : panel_action #must have instance_name and action in data, ex: panels/action instance_name=nino_dir action=list_users
        }
    }
    return paths

@tornado.gen.coroutine
def reset_panels(handler): 
    yield handler.config.deploy_handler.reset_panels()

@tornado.gen.coroutine
def new_panel(handler):
    states = yield handler.config.deploy_handler.get_states_data()
    print ('My data is : ', handler.data)
    panel = {'panel_name' : handler.data['panel_name'], 'role' : handler.data['role']}
    panel.update([x for x in states if x['name'] == handler.data['role']][0]['panels'])
    raise tornado.gen.Return(handler.config.deploy_handler.store_panel(panel))


@tornado.gen.coroutine
def list_panels(handler): 
    user_group = yield login.get_user_type(handler)

    print ('Listing panels for user: ', user_group)
    panels = yield handler.config.deploy_handler.datastore.get('panels')
    print ('Panels are : ', panels)
    panels = panels[user_group]

    raise tornado.gen.Return(panels)

@tornado.gen.coroutine
def panel_action_execute(handler):
    cl = salt.client.LocalClient()


    print ('Have localclient')
    instance = handler.data['instance_name']
    instance_info = yield apps.get_app_info(handler)
    print ('My info is : ', instance_info)
    state = instance_info[instance]['role']
    action = handler.data['action']


    args = handler.data.get('args', [])

    states = yield handler.config.deploy_handler.datastore.get('states')
    state = [x for x in states if x['name'] == state][0]

    result = cl.cmd(instance, state['module'] + '.' + action , args)
    raise tornado.gen.Return(result)


#@auth_only
@tornado.gen.coroutine
def panel_action(handler):
    instance_result = yield panel_action_execute(handler)
    handler.json(instance_result)


#@auth_only(user_allowed = True)
@tornado.gen.coroutine
def get_panels(handler):
    panels = yield list_panels(handler)
    handler.json(panels)


@auth_only(user_allowed = True)
@tornado.gen.coroutine
def get_panel_for_user(handler):
    try: 
        panel = handler.data['panel']
        user_panels = yield list_panels(handler)
        print ('Panel is : ', panel, 'and user panels are : ',  user_panels, 'with data : ', handler.data)
        panel = filter(lambda x: x['panel_name'] == handler.data['instance_name'], user_panels.get(panel, []))
        if panel: 
            panel = panel[0]
            handler.data['action'] = 'get_panel'
            try: 
                print ('Executing. ')
                panel = yield panel_action_execute(handler)
            except: 
                import traceback
                traceback.print_exc()

            print ('My panel is : ', panel)
            handler.json(panel)
        else: 
            raise tornado.gen.Return({'error' : 'Cannot get panel. '})

    except: 
        import traceback
        traceback.print_exc()




