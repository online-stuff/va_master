import json

import salt.client
import tornado.gen
import login

from login import auth_only

@tornado.gen.coroutine
def list_panels(handler): 
    user_group = yield login.get_user_type(handler)

    panels = yield handler.config.deploy_handler.datastore.get('init_vals')
    panels = panels['available_panels'][user_group]
#    if user_group == 'user': 
#        panels = [x for x in panels if x['user_allowed']]

    raise tornado.gen.Return(panels)

@tornado.gen.coroutine
def panel_action_execute(handler):
    cl = salt.client.LocalClient()

    print ('Handler data is : ', handler.data)

    instance = handler.data['instance_name'][0]
    state = handler.data['role'][0]
    action = handler.data['action'][0]

    states = yield handler.config.deploy_handler.datastore.get('states')
    state = [x for x in states if x['name'] == state][0]

    result = cl.cmd(instance, state['module'] + '.' + action)
    raise tornado.gen.Return(json.dumps(result))


@auth_only
@tornado.gen.coroutine
def panel_action(handler):
    yield panel_action_execute(handler)


@auth_only(user_allowed = True)
@tornado.gen.coroutine
def get_panels(handler):
    panels = list_panels(handler)
    handler.json(json.dumps(panels))


@auth_only(user_allowed = True)
@tornado.gen.coroutine
def get_panel_for_user(handler):
    panel = handler.data['panel']
    user_panels = yield list_panels(handler)
    print ('User panels : ', user_panels)

    if panel in user_panels: 
        print ('Panel is found. ')
        handler.data['action'] = 'get_panel'
        try: 
            panel = yield panel_action_execute(handler)
        except: 
            import traceback
            traceback.print_exc()

        print ('My panel is : ', panel)
        raise tornado.gen.Return(panel)
    raise tornado.gen.Return({'error' : 'Cannot get panel. '})


