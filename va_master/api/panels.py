import json

import salt.client
import tornado.gen
import login, apps

from login import auth_only

@tornado.gen.coroutine
def new_panel(handler):
    states = yield handler.config.deploy_handler.get_states_data()
    panel = {'panel_name' : handler.data['panel_name']}
    panel.update([x for x in states if x['name'] == handler.data['role']][0]['panels'])
    raise tornado.gen.Return(handler.config.deploy_handler.store_panel(panel))


@tornado.gen.coroutine
def list_panels(handler): 
    user_group = yield login.get_user_type(handler)

    panels = yield handler.config.deploy_handler.datastore.get('panels')
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

        user_panels = user_panels[handler.data['instance_name']]
        if panel in user_panels: 
            print ('Panel is found. ')
            handler.data['action'] = 'get_panel'
            try: 
                print ('Executing. ')
                panel = yield panel_action_execute(handler)
            except: 
                import traceback
                traceback.print_exc()

            print ('My panel is : ', panel)
            handler.json(panel)
        raise tornado.gen.Return({'error' : 'Cannot get panel. '})

    except: 
        import traceback
        traceback.print_exc()


