import json

import salt.client

import login

def panel_cmd(minion, action):
    cl = salt.client.LocalClient()
    result = cl.cmd(minion, action)
    raise tornado.gen.Return(result)

def panel_action(data):
    minion = handler.data['minion_name']
    action = handler.data['action']
    yield panel_cmd(minion, action)

def get_panels(handler):
    user = handler.data['user']
    user_group = login.get_user_type(user)
    panels = handler.config.deploy_handler.datastore.get('panel_types')['user_group']
    raise tornado.gen.Return(panels)

def get_panel_for_user(handler):
    user = handler.data['user']
    panel = handler.data['panel']
    user_panels = yield get_panels(handler)
    if panel in user_panels: 
        panel = get_panel(handler)
        raise tornado.gen.Return(panel)

def get_panel(handler):
    handler.data['action'] = 'get_panel'
    panel_json = panel_action(handler)
    raise tornado.gen.Return(panel_json)
