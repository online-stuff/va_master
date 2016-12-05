import json

import salt.client


def panel_cmd(minion, action):
    cl = salt.client.LocalClient()
    return cl.cmd(minion, action)

def panel_action(data):
    minion = handler.data['minion_name']
    action = handler.data['action']
    return panel_cmd(minion, action)

def get_panels(handler):
    user = handler.data['user']
    user_group = panel_cmd('va-directory', user)
    panels = handler.config.deploy_handler.datastore.get('panels')['user_group']
    return panels

def get_panel(handler):
    handler.data['action'] = 'get_panel'
    panel_json = panel_action(handler)
    return panel_json
