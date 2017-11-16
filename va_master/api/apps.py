from .login import auth_only
import tornado.gen
import json
import subprocess
import requests
import zipfile, tarfile

from tornado.concurrent import run_on_executor, Future

import salt_manage_pillar
from salt.client import Caller, LocalClient

import panels, services, providers

def get_paths():
    paths = {
        'get' : {
            'apps/set_settings' : {'function' : set_settings, 'args' : ['settings']},
            'apps/vpn_users' : {'function' : get_openvpn_users, 'args' : []},
            'apps/vpn_status' : {'function' : get_openvpn_status, 'args' : []},
            'apps/add_app' : {'function' : add_app, 'args' : ['provider', 'server_name']},

            'apps/get_user_salt_functions' : {'function' : get_user_salt_functions, 'args' : ['dash_user']},
            'apps/get_all_salt_functions' : {'function' : get_all_salt_functions, 'args' : []},

            'states' : {'function' : get_states, 'args' : ['handler', 'dash_user']},

        },
        'post' : {
            'state/add' : {'function' : create_new_state,'args' : ['file', 'body', 'filename']},
            'apps/new/validate_fields' : {'function' : validate_app_fields, 'args' : ['handler']},
            'apps' : {'function' : launch_app, 'args' : ['handler']},
            'apps/action' : {'function' : perform_server_action, 'args' : ['handler', 'provider_name', 'action', 'server_name']},
            'apps/add_vpn_user': {'function' : add_openvpn_user, 'args' : ['username']},
            'apps/revoke_vpn_user': {'function' : revoke_openvpn_user, 'args' : ['username']},
            'apps/list_user_logins': {'function' : list_user_logins, 'args' : ['username']},
            'apps/download_vpn_cert': {'function' : download_vpn_cert, 'args' : ['username', 'handler']},
        }
    }
    return paths


def bytes_to_readable(num, suffix='B'):
    """Converts bytes integer to human readable"""

    num = int(num)
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

@tornado.gen.coroutine
def add_app(provider, server_name):
    "WIP function - TODO make adding apps work properly"""

    app = yield get_app_info(server_name)
    yield handler.config.deploy_handler.store_app(app, provider)

@tornado.gen.coroutine
def get_openvpn_users():
    """Gets openvpn users and current status. Then merges users to find currently active ones and their usage data. """

    salt_caller = Caller()
    openvpn_users = salt_caller.cmd('openvpn.list_users')

    #openvpn_users returns {"revoked" : [list, of, revoked, users], "active" : [list, of, active, users], "status" : {"client_list" : [], "routing_table" : []}}
    #We want to convert it to {"revoked" : [], "status" : [client, list], active" : [{"name" : "", "check" : False, "connected" : True/False}]}

    users = {'revoked' : openvpn_users['revoked']}
    users_names = [i['Common Name'] for i in openvpn_users['status']['client_list']]
    users['active'] = [{'name' : x, 'check' : False, 'connected' : x in users_names} for x in openvpn_users['active']]
    users['status'] = openvpn_users['status']['client_list'] or []

    #Virtual address is missing from client_list, we have to find it in the routing table and update it. 
    for x in openvpn_users['status']['client_list']:
        x.update({
            'Real Address' : [y.get('Virtual Address') for y in openvpn_users['status']['routing_table'] if y['Real Address'] == x['Real Address']][0]
        })
       
    #Make bytes human readable
    for k in ['Bytes Received', 'Bytes Sent']:
        for x in openvpn_users['status']['client_list']:
            x[k] = bytes_to_readable(x[k])

    raise tornado.gen.Return(users)

@tornado.gen.coroutine
def get_openvpn_status():
    """Just gets the openvpn status information, which lists the current clients. """

    cl = Caller()
    status = cl.cmd('openvpn.get_status')
    raise tornado.gen.Return(status)

@tornado.gen.coroutine
def add_openvpn_user(username):
    """Creates a new openvpn user. """

    cl = Caller()
    success = cl.cmd('openvpn.add_user', username = username)
    raise tornado.gen.Return(success)

@tornado.gen.coroutine
def revoke_openvpn_user(username):
    "Revokes an existing vpn user"""

    cl = Caller()
    success = cl.cmd('openvpn.revoke_user', username = username)
    raise tornado.gen.Return(success)   

@tornado.gen.coroutine
def list_user_logins(username): 
    """Provides a list of previous openvpn logins. """

    cl = Caller()
    success = cl.cmd('openvpn.list_user_logins', user = username)
    raise tornado.gen.Return(success)

@tornado.gen.coroutine
def download_vpn_cert(username, handler):
    """Downloads the vpn certificate for the required user. Works by copying the file to /tmp/{username}_vpn.cert and then serving it through Tornado. """

    cl = Caller()
    cert = cl.cmd('openvpn.get_config', username = username)

    vpn_cert_path = '/tmp/' + username + '_vpn.cert'
    with open(vpn_cert_path, 'w') as f: 
        f.write(cert)
 
    handler.serve_file(vpn_cert_path)
    raise tornado.gen.Return({'data_type' : 'file'})


@tornado.gen.coroutine
def perform_server_action(handler, provider_name, action, server_name): 
    """Calls required action on the server through the driver. """

    provider, driver = yield providers.get_provider_and_driver(handler, provider_name) 
    success = yield driver.server_action(provider, server_name, action)
    raise tornado.gen.Return(success)


@tornado.gen.coroutine
def get_states(handler, dash_user):
    """
    Gets all states from the datastore. The state data is retrieved from the appinfo.json files in their respective folders. 
    Each appinfo has needs to have a name, description, version, icon, dependency, substate and path field. It should optionaly have a module and panels field, if the state is intended to be used with panels, but these are optional. 
    """
    
    datastore_handler = handler.datastore_handler
    states_data = yield datastore_handler.get_states()
    panels_data = yield panels.get_panels(handler, dash_user)

    default_panels = {'admin' : [], 'user' : []}

    for state in states_data: 
        state_panel = [x for x in panels_data if x['name'] == state['name']][0]
        state['servers'] = state_panel['servers']
        state['panels'] = state.get('panels', default_panels)[dash_user['type']]
    raise tornado.gen.Return(states_data)

#WIP function - TODO check if it still works properly. 
@tornado.gen.coroutine
def create_new_state(deploy_handler, file_contents, body, filename):
    """Creates a new state from a file, unpack it to the state directory and add it to the datastore. """

    data = file_contents[0]
    files_archive = data['body']
    state_name = data['filename']

    #TODO maybe get it from config? 
    salt_path = '/srv/salt/'
    tmp_archive = '/tmp/' + state_name 

    with open(tmp_archive, 'w') as f:
        f.write(files_archive)

    new_state = {
        'name' : data['name'],
        'version' : data['version'],
        'description' : data['description'], 
        'icon' : data['icon'], 
        'dependency' : data['dependency'], 
        'path' : data['path'],
        'substates' : data['substates']
    }

    with open(salt_path + tar_ref.getnames()[0] + '/appinfo.json', 'w') as f: 
        f.write(json.dumps(new_state))

#    zip_ref = zipfile.ZipFile(tmp_archive)
#    zip_ref.extractall(salt_path)

    tar_ref = tarfile.TarFile(tmp_archive)
    tar_ref.extractall(salt_path)

#    zip_ref.close()
    tar_ref.close()
#    manage_states(handler, 'append')


@tornado.gen.coroutine
def validate_app_fields(handler):
    #TODO finish documentation
    """
    Creates a server by going through a validation scheme similar to that for adding providers. 
    Requires that you send a step index as an argument, whereas the specifics for the validation are based on what driver you are using. 
    If no provider_name is sent, creates a server on the va_standalone_servers provider, which is mostly invisible, and its servers are treated as standalone. 
    """
    deploy_handler = handler.deploy_handler

    provider, driver = yield providers.get_provider_and_driver(handler, handler.data.get('provider_name', 'va_standalone_servers'))

    kwargs = handler.data
    step = handler.data.pop('step')

    fields = yield driver.validate_app_fields(step, **kwargs)
    if not fields: 
        raise Exception('Some fields were not entered properly. ')

    print ('In driver : ', driver)
    # If the state has extra fields, then there are 3 steps, otherwise just 2. 
    if step == 3: 
        handler.data.update(fields)
        try:
            print ('In validate, will launch. ')
            result = yield handler.executor.submit(launch_app, handler)
        except: 
            import traceback
            traceback.print_exc()
    print ('Fields : ', fields)
    raise tornado.gen.Return(fields)


@tornado.gen.coroutine
def get_app_info(server_name):
    """Gets mine inventory for the provided instance. """

    cl = Caller()
    server_info = cl.cmd('mine.get', server_name, 'inventory') 
    server_info = server_info.get(server_name)
    raise tornado.gen.Return(server_info)


def write_pillar(data):
    """Writes the supplied data as a yaml file in to a credentials file and adds it to the top credentials. """

    pillar_path = '/srv/pillar/%s-credentials.sls' % (data.get('server_name'))
    with open(pillar_path, 'w') as f: 
        pillar_str = ''

        #We need a pillar that looks like this: 
        #field1: some_value
        #field2: some_other_value

        for field in data.get('extra_fields'): 
            pillar_str += '%s: %s\n' % (field, data['extra_fields'][field])
        f.write(pillar_str)
    salt_manage_pillar.add_server(data.get('server_name'), data.get('role', ''))

        
def add_panel_for_minion(handler, data, minion_info):
    """Adds a panel for a minion based on its appinfo.json file and minion info retrieved from salt. """

    init_vals = yield store.get('init_vals')
    states = init_vals['states']
    state = [x for x in states if x['name'] == data['role']][0]
      
    print ('Minion info is : ', minion_info['role'])
    panel = {'panel_name' : data['server_name'], 'role' : minion_info['role']}
    panel.update(state['panels'])
    yield handler.config.datastore_handler.store_panel(panel)

##@auth_only
@tornado.gen.coroutine
def launch_app(handler):
    """
    Launches a server based on the data supplied. 
    If the extra_fields key is supplied, it will create a specific pillar for the server. 
    If provider_name is not sent, it will create a va_standalone server, with the invisible driver va_standalone_servers. 
    """
    #TODO finish documentation

    data = handler.data
    try:
        provider, driver = yield providers.get_provider_and_driver(handler, data.get('provider_name', 'va_standalone_servers'))
    
        if data.get('extra_fields', {}) : 
            write_pillar(data)

        print ('Launching with : ', data, ' with provider : ', provider, ' and driver : ', driver)
        result = yield driver.create_server(provider, data)
    except: 
        import traceback
        traceback.print_exc()

    if data.get('role', True):

        minion_info = None

        retries = 0
        while not minion_info and retries < int(handler.data.get('mine_retries', '10')):
            minion_info = yield get_app_info(handler.data['server_name'])
            minion_info.update({'type' : 'app'})
            retries += 1
            if not minion_info: 
                yield tornado.gen.sleep(10)

        yield services.add_services_presets(minion_info, ['ping'])

        add_panel_for_minion(data, minion_info)

        if not minion_info: 
            raise tornado.gen.Return({"success" : False, "message" : "No minion_info, something probably went wrong with trying to start the instance. ", "data" : None})

    raise tornado.gen.Return(result)

#WIP - todo finish this function
@tornado.gen.coroutine
def get_all_salt_functions(deploy_handler):
    """ Gets all salt functions for all minions. """
    cl = LocalClient()
    states = yield deploy_handler.get_states()

    functions = cl.cmd('*', 'sys.doc')
    result = {
        [i for i in x if x[states[x]['module']] in i] 
    for x in functions}

    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_user_salt_functions(deploy_handler, dash_user):
    """Gets all functions tagged as 'salt' from the datastore for the logged in user. """

    salt_functions = yield deploy_handler.get_user_salt_functions(dash_user['username'])
    raise tornado.gen.Return(salt_functions)
    
@tornado.gen.coroutine
def add_user_salt_functions(deploy_handler, dash_user, functions):
    """Adds the list of salt functions for use for the logged in user. """

    yield deploy_handler.add_user_salt_functions(dash_user['username'], functions)

@tornado.gen.coroutine
def set_settings(settings):
    pillar_file = '/srv/pillar/nekoj.sls'
    with open(pillar_file, 'r') as f:
        a = yaml.load(f.read())

    a.update(settings)

    with open(pillar_file, 'w') as f:
        f.write(yaml.dump(a, default_flow_style=False))


