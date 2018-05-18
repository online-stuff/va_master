import tornado
from salt.client import LocalClient
from salt_handler import add_minion_to_server
from va_master.api import panels #May result in circular imports, maybe want to resort to just using datastore_handler directlry. 

@tornado.gen.coroutine
def handle_app(datastore_handler, server_name, role):
    ''' Helping function for the manage_server_type function. If a server is added as an app, it adds a panel, sets the type, calls add_minion_to_server, which installs salt and runs highstate, and then inserts the server to the datastore. '''

    if not role: 
        raise Exception('Tried to convert ' + str(server_name) + " to app, but the role argument is empty. ")

    server = yield datastore_handler.get_object(object_type = 'server', server_name = server_name)

    server['type'] = 'app'
    server['available_actions'] = server.get('available_actions', {}) # TODO get panel actions and add here

    cl = LocalClient()
    highstate = cl.cmd(server_name, 'state.highstate')
    print ('Highstate is : ', highstate)

    yield panels.new_panel(datastore_handler, server_name = server_name, role = role)

    raise tornado.gen.Return(server)

@tornado.gen.coroutine
def handle_ssh(datastore_handler, server, ip_address, username):
    user_type = 'root' if username == 'root' else 'user'
    new_subtype = user_type
    new_type = 'ssh'

    server['%s_user_type' % new_type] = user_type
    server['ip_address'] = ip_address or server.get('ip_address')
    server['username'] = username
    server = yield update_server(datastore_handler, server, new_type, new_subtype)
    raise tornado.gen.Return(server)

@tornado.gen.coroutine
def handle_provider(datastore_handler, provider_name = None, driver_name = None):
    if provider_name: 
        provider = yield datastore_handler.get_provider(provider_name = provider_name)
        server['provider_name'] = provider_name
        driver_name = provider['driver_name']
    if not driver_name: 
        raise Exception('Tried to manage server with provider, but neither driver_name nor provider_name was sent. ')

    new_type = 'provider'
    new_subtype = driver_name
    server_drivers = server.get('drivers', []) + [driver_name]
    server['drivers'] = list(set(server_drivers))
    server = yield update_server(datastore_handler, server, new_type, new_subtype)
    raise tornado.gen.Return(server)

@tornado.gen.coroutine
def handle_salt(datastore_handler, server):
    minion_kwargs = {'username' : server['username']}

    if server.get('password'): minion_kwargs['password'] = server['password']
    else: minion_kwargs['key_filename'] = datastore_handler.config.ssh_key_path + datastore_handler.config.ssh_key_name + '.pem'

    yield add_minion_to_server(datastore_handler, server['server_name'], server['ip_address'], role = None, **minion_kwargs)

    server = yield update_server(datastore_handler, server, new_type = 'salt', new_subtype = '')
    raise tornado.gen.Return(server)

@tornado.gen.coroutine
def update_server(datastore_handler, server, new_type, new_subtype):
    server['type'] = 'managed'
    server['managed_by'] = list(set(server.get('managed_by', []) + [new_type]))

    type_actions = yield datastore_handler.get_object(object_type = 'managed_actions', manage_type = new_type, manage_subtype = new_subtype)
    server['type'] = 'managed'
    server['managed_by'] = list(set(server.get('managed_by', []) + [new_type]))
    server['available_actions'] = server.get('available_actions', {})
    server['available_actions'][new_type] = type_actions['actions']
    raise tornado.gen.Return(server)


#TODO make winexe work
@tornado.gen.coroutine
def manage_server_type(datastore_handler, server_name, new_type, ip_address = None, username = None, driver_name = None, provider_name = None, role = None, kwargs = {}):
    ''' Updates a server's managed_by, type and available_actions fields in the datastore. If the function is making a server into managed_by: ssh, then the ip_address and username fields are also saved. If it is a provider, the drivers: field is updated. If it is an app, it installs salt, runs highstate and adds a panel. '''

    server = yield datastore_handler.get_object(object_type = 'server', server_name = server_name)
    server.update(kwargs)

    if new_type == 'ssh':
        server = yield handle_ssh(datastore_handler, server, ip_address, username)

    elif new_type == 'provider':
        server = yield handle_provider(datastore_handler, provider_name = None, driver_name = None)

    elif new_type == 'salt' : 
        server = yield handle_salt(datastore_handler, server)

    elif new_type == 'app':
        server = yield handle_app(datastore_handler, server_name = server_name, role = role)

    print ('Inserting ', server, ' in ', server_name)
    yield datastore_handler.insert_object(object_type = 'server', data = server, server_name = server_name)
    raise tornado.gen.Return(server)
