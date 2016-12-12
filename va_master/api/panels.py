import json

import salt.client
import tornado.gen
import login

from login import auth_only

@tornado.gen.coroutine
def list_panels(handler): 
    user_group = yield login.get_user_type(handler)

    panels = yield handler.config.deploy_handler.datastore.get('panel_types')
    panels = panels[user_group]

    raise tornado.gen.Return(panels)



@tornado.gen.coroutine
def panel_action_execute(handler):
    cl = salt.client.LocalClient()

    minion = handler.data['minion_name'][0]
    state = handler.data['state'][0]
    action = handler.data['action'][0]

    states = yield handler.config.deploy_handler.datastore.get('states')
    state = [x for x in states if x['name'] == state][0]

    result = cl.cmd(minion, state['module'] + '.' + action)
    raise tornado.gen.Return(json.dumps(result))


@auth_only(user_allowed = True)
@tornado.gen.coroutine
def get_panels(handler):
    panels = list_panels(handler)
    handler.json(json.dumps(panels))

@auth_only
@tornado.gen.coroutine
def panel_action(handler):
    yield panel_action_execute(handler)

@tornado.gen.coroutine
@auth_only(user_allowed = True)
def get_panel_for_user(handler):
    panel = handler.data['panel']
    user_panels = yield list_panels(handler)

    if panel in user_panels: 
        panel = panel_action_execute(handler)
        handler.data['action'] = 'get_panel'

        panel_json = panel_action(handler)

        handler.json(panel_json)
#        raise tornado.gen.Return(panel)
    handler.json({'error' : 'Cannot get panel. '}, 401)

def get_panel(handler):
    raise tornado.gen.Return(panel_json)
