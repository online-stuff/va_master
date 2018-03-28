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
from paramiko import SSHClient, AutoAddPolicy

def get_paths():
    paths = {
        'get' : {
            'apps/set_settings' : {'function' : set_settings, 'args' : ['settings']},
            'apps/vpn_users' : {'function' : get_openvpn_users, 'args' : []},
            'apps/vpn_status' : {'function' : get_openvpn_status, 'args' : []},
#            'apps/add_app' : {'function' : add_app, 'args' : ['provider', 'server_name']},

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
            'servers/add_server' :  {'function' : add_server_to_datastore, 'args' : ['datastore_handler', 'server_name', 'ip_address', 'hostname', 'manage_type', 'user_type', 'driver_name']},
            'servers/manage_server' : {'function' : manage_server_type, 'args' : ['datastore_handler', 'server_name', 'new_type', 'username', 'driver_name', 'role']},
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
    yield handler.config.datastore_handler.store_app(app, provider)

@tornado.gen.coroutine
def get_openvpn_users():
    """Gets openvpn users and current status. Then merges users to find currently active ones and their usage data. """

    salt_caller = Caller()
    openvpn_users = salt_caller.cmd('openvpn.list_users')

    if type(openvpn_users) != str: 
        print ('Openvpn users result : ', openvpn_users)
        raise Exception("Could not get openvpn users list. Contact your administrator for more information. ")

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
    if success:
        print ('Adding user returned : ', success)
        raise Exception('Adding an openvpn user returned with an error. ')
    raise tornado.gen.Return({'success' : True, 'data' : None, 'message' : 'User added successfuly. '})

@tornado.gen.coroutine
def revoke_openvpn_user(username):
    "Revokes an existing vpn user"""

    cl = Caller()
    success = cl.cmd('openvpn.revoke_user', username = username)

    if success:
        print ('Revoking user returned : ', success)
        raise Exception('Revoking %s returned with an error. ' % (username))
    raise tornado.gen.Return({'success' : True, 'data' : None, 'message' : 'User revoked successfuly. '})

    raise tornado.gen.Return(success)   

@tornado.gen.coroutine
def list_user_logins(username): 
    """Provides a list of previous openvpn logins. """

    cl = Caller()
    success = cl.cmd('openvpn.list_user_logins', user = username)
    if type(success) == str:
        print ('User logins returned', success)
        raise Exception('Listing user logins returned with an error. ')
    raise tornado.gen.Return(success)

@tornado.gen.coroutine
def download_vpn_cert(username, handler):
    """Downloads the vpn certificate for the required user. Works by copying the file to /tmp/{username}_vpn.cert and then serving it through Tornado. """

    cl = Caller()
    cert = cl.cmd('openvpn.get_config', username = username)

    cert_has_error = yield handler.has_error(cert)
    if cert_has_error:
        print ('Cert has an error: ', cert)
        raise Exception('Getting certificate for %s returned with an error. ' % (username))

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
        state_panel = [x for x in panels_data if x['name'] == state['name']]
        if not state_panel: 
            raise Exception('%s was not found in the list of states : %s', (state['name'], str([x['name'] for x in panels_data])))
        state_panel = state_panel[0]
        state['servers'] = state_panel['servers']
        state['panels'] = state.get('panels', default_panels)[dash_user['type']]
    raise tornado.gen.Return(states_data)

#WIP function - TODO check if it still works properly. 
@tornado.gen.coroutine
def create_new_state(datastore_handler, file_contents, body, filename):
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

    yield datastore_handler.add_state(new_state)

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
    provider, driver = yield providers.get_provider_and_driver(handler, handler.data.get('provider_name', 'va_standalone_servers'))

    kwargs = handler.data
    step = handler.data.pop('step')

    fields = yield driver.validate_app_fields(step, **kwargs)

    # If the state has extra fields, then there are 3 steps, otherwise just 2. 
    if step == 3: 
        handler.data.update(fields)
        try:
            result = yield handler.executor.submit(launch_app, handler)
        except: 
            import traceback
            traceback.print_exc()
    raise tornado.gen.Return(fields)


@tornado.gen.coroutine
def get_app_info(server_name):
    """Gets mine inventory for the provided instance. """

    cl = Caller()
    server_info = cl.cmd('mine.get', server_name, 'inventory') 
    server_info = server_info.get(server_name)
    if not server_info: 
        raise Exception('Attempted to get app info for %s but mine.get returned empty. ' % (server_name))
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

    yield add_server_to_datastore(handler.datastore_handler, server_name = data['server_name'], hostname = data['server_name'], manage_type = 'provider', driver_name = provider['driver_name'])

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

        if not minion_info: 
            raise tornado.gen.Return({"success" : False, "message" : "No minion_info, something probably went wrong with trying to start the instance. ", "data" : None})
        else: 
            yield manage_server_type(handler.datastore_handler, server_name = data['server_name'], new_type = 'app', role = data['role'])

    raise tornado.gen.Return(result)

#WIP - todo finish this function
@tornado.gen.coroutine
def get_all_salt_functions(datastore_handler):
    """ Gets all salt functions for all minions. """
    cl = LocalClient()
    states = yield datastore_handler.get_states()

    functions = cl.cmd('*', 'sys.doc')
    result = {
        [i for i in x if x[states[x]['module']] in i] 
    for x in functions}

    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_user_salt_functions(datastore_handler, dash_user):
    """Gets all functions tagged as 'salt' from the datastore for the logged in user. """

    salt_functions = yield datastore_handler.get_user_salt_functions(dash_user['username'])
    raise tornado.gen.Return(salt_functions)
    
@tornado.gen.coroutine
def add_user_salt_functions(datastore_handler, dash_user, functions):
    """Adds the list of salt functions for use for the logged in user. """

    yield datastore_handler.add_user_salt_functions(dash_user['username'], functions)

@tornado.gen.coroutine
def set_settings(settings):
    pillar_file = '/srv/pillar/nekoj.sls'
    with open(pillar_file, 'r') as f:
        a = yaml.load(f.read())

    a.update(settings)

    with open(pillar_file, 'w') as f:
        f.write(yaml.dump(a, default_flow_style=False))


@tornado.gen.coroutine
def add_server_to_datastore(datastore_handler, server_name, ip_address = None, hostname = None, manage_type = None, username = None, driver_name = None, kwargs = {}):
    server = {}
    for attr in ['ip_address', 'hostname']: 
        server[attr] = locals()[attr]

    server['available_actions'] = {}

    yield datastore_handler.insert_object(object_type = 'server', server_name = server_name, data = server)

    if manage_type: 
        print ('Calling with ', datastore_handler, server_name, manage_type, username, driver_name, kwargs)
        server = yield manage_server_type(datastore_handler, server_name, manage_type, username = username, driver_name = driver_name, kwargs = kwargs)

    raise tornado.gen.Return(server)


@tornado.gen.coroutine
def handle_app(datastore_handler, server_name, role):
    if not role: 
        raise Exception('Tried to convert ' + str(server_name) + " to app, but the role argument is empty. ")

    server = yield datastore_handler.get_object(object_type = 'server', server_name = server_name)
    yield panels.new_panel(datastore_handler, server_name = server_name, role = role)

    server['type'] = 'app'
    server['managed_by'] = list(set(server.get('managed_by', []) + ['app']))
    server['available_actions'] = server.get('available_actions', []) + [] # TODO get panel actions and add here

    yield datastore_handler.insert_object(object_type = 'server', data = server, server_name = server_name)

    raise tornado.gen.Return(server)


def test_ssh(username, ip_address, password = None, port = None):
    cl = SSHClient()
    cl.load_system_host_keys()
    cl.set_missing_host_key_policy(AutoAddPolicy())
    connect_kwargs = {
        'username' : username, 
    }
    key_path = "TODO"

    if data.get('port'): 
        connect_kwargs['port'] = int(port)

    if data.get('password'): 
        connect_kwargs['password'] = password
    else: 
        connect_kwargs['key_filename'] = key_path + '.pem'

    print ('Attempting connect with : ', connect_kwargs)
    cl.connect(data.get('ip'), **connect_kwargs)


@tornado.gen.coroutine
def manage_server_type(datastore_handler, server_name, new_type, username = None, driver_name = None, role = None, kwargs = {}):
    user_type = 'root' if username == 'root' else 'user'
    server = yield datastore_handler.get_object(object_type = 'server', server_name = server_name)

    new_subtype = None
    if new_type in ['ssh', 'winexe']:
        new_subtype = user_type
        server['%s_user_type' % new_type] = user_type
    elif new_type in ['provider']: 
        new_subtype = driver_name
        server['drivers'] = server.get('drivers', []) + [driver_name]
    elif new_type == 'app': 
        server_data = yield handle_app(datastore_handler, server_name = server_name, role = role)
        raise tornado.gen.Return(server_data)

    if not new_subtype: 
        raise Exception("Tried to change " + str(server_name) + " type to " + str(new_type) + " but could not get subtype. If managing with provider, make sure to set `driver_name`, if managing with SSH or winexe, set `user_type`")

    type_actions = yield datastore_handler.get_object(object_type = 'managed_actions', manage_type = new_type, manage_subtype = new_subtype)
    server['type'] = 'managed'
    server['managed_by'] = list(set(server.get('managed_by', []) + [new_type]))
    server['available_actions'] = server.get('available_actions', {})
    server['available_actions'][new_type] = type_actions['actions']
    server.update(kwargs)

    yield datastore_handler.insert_object(object_type = 'server', data = server, server_name = server_name)
    raise tornado.gen.Return(server)
