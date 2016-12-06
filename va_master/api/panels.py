import json

import salt.client
import tornado.gen
import login

from login import auth_only

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

@tornado.gen.coroutine
def get_panels(handler):
    user = handler.data['user']
    user_group = login.get_user_type(user)
    panels = handler.config.deploy_handler.datastore.get('panel_types')['user_group']
    raise tornado.gen.Return(panels)

@auth_only
@tornado.gen.coroutine
def panel_action(handler):
    yield panel_action_execute(handler)

@auth_only(user_allowed = True)
@tornado.gen.coroutine
def get_panel_for_user(handler):
    user = handler.data['user']
    panel = handler.data['panel']
    user_panels = yield get_panels(handler)
    if panel in user_panels: 
        panel = panel_action_execute(handler)
        raise tornado.gen.Return(panel)
    handler.json({'error' : 'Cannot get panel. '}, 401)

def get_panel(handler):
    handler.data['action'] = 'get_panel'
    panel_json = panel_action(handler)
    raise tornado.gen.Return(panel_json)
