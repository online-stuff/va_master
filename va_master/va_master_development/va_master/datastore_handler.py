import json, glob, yaml, datetime
import requests
import subprocess
import traceback
import tornado
import tornado.gen

from pbkdf2 import crypt

#def compare_dicts(d1, d2):
#    for key in d1:
#        if key not in d2 or type(d1.get(key)) != type(d2.get(key)):
#            return False
#
#        if type(d1[key]) == dict:
#            if not compare_dicts(d1[key], d2[key]):
#                return False
#        elif type(d1[key] == list):
#            if all([type(x) == dict for x in d1[key]): 
#                if not all([compare_dicts(

class DatastoreHandler(object):

    def __init__(self, datastore, datastore_spec_path):
        self.datastore = datastore

        with open(datastore_spec_path) as f: 
            spec = f.read()
            self.spec = json.loads(spec)


    #The datastore spec contains handles using python's string formatting. For instance 'providers/%s'. 
    #handle_keys is a list of values to be formatted in the string, for instance 'providers/%s' % 'va_generic_driver'. 
    #TODO determine which is better (using the first one atm)- 
    #insert_object('provider', data = {...}, provider_name = 'some_provider')
    # --- OR ---
    #insert_object('provider', data = {...}, handle_data = {'provider_name' : 'some_provider})
    @tornado.gen.coroutine
    def insert_object(self, object_type, data = {}, **handle_data):
        new_object_spec = self.spec[object_type]

        handle_data = handle_data.get('handle_data', handle_data)
        new_object_handle = new_object_spec['consul_handle'].format(**handle_data)

        #TODO check data to be as designed in the spec
        new_object = data

        print ('Inserting : ', new_object, ' at : ', new_object_handle)
        yield self.datastore.insert(new_object_handle, new_object)

    @tornado.gen.coroutine
    def get_object(self, object_type, **handle_data):
        object_spec = self.spec[object_type]
        object_handle = object_spec['consul_handle'].format(**handle_data)
        result = yield self.datastore.get(object_handle)
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def delete_object(self, object_type, **handle_data):
        object_spec = self.spec[object_type]
        object_handle = object_spec['consul_handle'].format(**handle_data)
        result = yield self.datastore.delete(object_handle)
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def get_provider(self, provider_name):
        provider = yield self.get_object('provider', provider_name = provider_name)
        raise tornado.gen.Return(provider)

    @tornado.gen.coroutine
    def get_triggers(self, provider_name):
        provider = yield self.get_provider(provider_name)
        raise tornado.gen.coroutine(provider.get('triggers', []))

    @tornado.gen.coroutine
    def get_hidden_servers(self):
        try:
            servers = yield self.datastore.get('hidden_servers')
        except: 
            yield self.datastore.insert('hidden_servers', [])
            servers = []

        servers += ['va_standalone_servers']
        raise tornado.gen.Return(servers)


    @tornado.gen.coroutine
    def get_provider_and_driver(self, provider_name):
        provider = yield self.get_provider(provider_name)
        driver = provider['driver_id']

    @tornado.gen.coroutine
    def list_providers(self):
        providers = yield self.datastore.get_recurse('providers/')
        raise tornado.gen.Return(providers)

    @tornado.gen.coroutine
    def get_triggers(self, provider_name):
        provider = yield self.get_provider(provider_name) 
        raise tornado.gen.Return(provider.get('triggers', []))

    @tornado.gen.coroutine
    def create_provider(self, field_values):
        print ('Creating provider with : ', field_values)
        yield self.insert_object('provider', data = field_values, provider_name = field_values['provider_name'])

    @tornado.gen.coroutine
    def delete_provider(self, provider_name):
        yield self.delete_object('provider', provider_name = provider_name)

    @tornado.gen.coroutine
    def add_generic_server(provider_name, base_server):
        generic_server = yield self.get_provider(provider_name)
        generic_server['instances'].append(base_server)

    @tornado.gen.coroutine
    def store_action(self, user, path, data):
        try: 
            actions = yield self.datastore.get('actions')
        except: 
            actions = []
        actions.append({
            'username' : user['username'], 
            'type' : user['type'], 
            'path' : path, 
            'data' : str(data), 
            'time' : str(datetime.datetime.now())
        })
        yield self.datastore.insert('actions', actions)

    @tornado.gen.coroutine
    def get_actions(self, number_actions, filters = {}):
        all_actions = yield self.datastore.get('actions')
        actions = all_actions[:number_actions] if number_actions else all_actions
        raise tornado.gen.Return(all_actions[:number_actions])

    @tornado.gen.coroutine
    def get_users(self, user_type = 'users'):
        users = yield self.datastore.get_recurse(user_type + '/')
        users = [x['username'] for x in users]
        raise tornado.gen.Return(users)


    @tornado.gen.coroutine
    def update_user(self, user, password):
        edited_user = yield self.get_object('user', username = user)

        crypted_pass = crypt(password)
        edited_user['password'] = crypted_pass
        yield self.insert_object('user', data = edited_user, username = user) 

    @tornado.gen.coroutine
    def delete_user(self, user):
        yield self.datastore.delete('users/' + user)

    @tornado.gen.coroutine
    def set_user_functions(self, user, functions):
        edited_user = yield self.get_object('user', username = user)

        functions = [{"func_path" : x.get('value')} if x.get('value') else x for x in functions]
        print ('Functions are : ', functions)
        edited_user['functions'] = functions 
        yield self.insert_object('user', data = edited_user, username = user) 


    @tornado.gen.coroutine
    def add_user_functions(self, user, functions):
        edited_user = yield self.get_object('user', username = user)
        functions += edited_user.get('functions', [])

        yield self.set_user_functions(user, functions)

    @tornado.gen.coroutine
    def get_user_functions(self, user, func_type = ''):
        user = yield self.get_object('user', username = user)

        user_funcs = user.get('functions', [])

        #Get all functions from the user groups to return in a single list. 
        #i.e. instead of [{group_name : group, functions : [{group_func1}, ...]}, func1, func2, ...] we want [group_func1, ..., func1, func2, ...]
#        user_group_functions = [x['functions'] for x in user_funcs if x.get('func_type', '') == 'function_group']

#        user_funcs = [
#            x.get('func_path') for x in user_funcs + user_group_functions 
#        if x.get('func_type', '') == func_type and x.get('func_path')]

        raise tornado.gen.Return(user_funcs)

    @tornado.gen.coroutine
    def get_user(self, username, user_type = 'user'):
        try:
            user = yield self.get_object(user_type, username = username)
        except: 
            user = None

        raise tornado.gen.Return(user)

    @tornado.gen.coroutine
    def find_user(self, username):
        for user_type in ['user', 'admin']:
            user = yield self.get_user(username, user_type)
            if user: 
                user['user_type'] = user_type
                raise tornado.gen.Return(user)

    @tornado.gen.coroutine
    def get_panels(self, user_type):
        panels = yield self.datastore.get_recurse('panels/' + user_type)
        raise tornado.gen.Return(panels)

    @tornado.gen.coroutine
    def store_panel(self, panel, user_type, name = ''):
        if not name: name = panel['name']
        panel_type = user_type + '_panel'
        yield self.insert_object(panel_type, data = panel, name = name)

    @tornado.gen.coroutine
    def get_panel(self, name, user_type = 'user'):
        panel_type = user_type + '_panel'
        panel = yield self.get_object(panel_type, name = name)

        raise tornado.gen.Return(panel)

    @tornado.gen.coroutine
    def add_panel(self, panel_name, role):
        states = yield self.get_states_data()
        panel_state = [x for x in states if x['name'] == role][0]

        user_panel = yield self.get_panel(role, 'user')
        admin_panel = yield self.get_panel(role, 'admin')

        user_panel['servers'].append(panel_name)
        admin_panel['servers'].append(panel_name)

        yield self.store_panel('user', user_panel, role)
        yield self.store_panel('admin', admin_panel, role)

    @tornado.gen.coroutine
    def get_states_data(self, states = []):
        states_data = []
        subdirs = glob.glob('/srv/salt/*')
        for state in subdirs:
            try:
                with open(state + '/appinfo.json') as f:
                    print ('Opening ', state)
                    states_data.append(json.loads(f.read()))
            except IOError as e:
                print (state, ' does not have an appinfo file, skipping. ')
            except:
                print ('error with ', state)
                import traceback
                traceback.print_exc()

        if states:
            states_data = [x for x in states_data if x['name'] in states]

        raise tornado.gen.Return(states_data)

    @tornado.gen.coroutine
    def import_states_from_states_data(self, states = []):
        print ('Importing. ')
        states_data = yield self.get_states_data(states)

        empty_panel = {'admin' : [], 'user' : []}

        for state in states_data: 
            for user_type in ['admin', 'user']: 
 
                old_panel = yield self.get_panel(name = state['name'])
                panel = {
                    'name' : state['name'], 
                    'icon' : state['icon'], 
                    'servers' : old_panel['servers'],
                    'panels' : state.get('panels', empty_panel)[user_type]
                }
                yield self.store_panel(panel, user_type)
            print ('Storing : ', state)
            yield self.store_state(state)

        raise tornado.gen.Return(states_data)

    @tornado.gen.coroutine
    def get_states(self):
        states = yield self.datastore.get_recurse('state/')
        raise tornado.gen.Return(states)

    @tornado.gen.coroutine
    def store_state(self, state):
        yield self.insert_object('state', state, name = state['name'])

    @tornado.gen.coroutine
    def get_state(self, name):
        state = yield self.get_object('state', name = name)
        raise tornado.gen.Return(state)

    @tornado.gen.coroutine
    def create_user(self, user_data, user_type = 'user'):
        yield self.insert_object(user_type, data = user_data, username = user_data['username'])

    @tornado.gen.coroutine
    def get_user_groups(self):
        groups = yield self.datastore.get_recurse('user_groups/')
        raise tornado.gen.Return(groups)

    @tornado.gen.coroutine
    def get_user_group(self, group_name):
        group = yield self.get_object('user_group', group_name = group_name)
        raise tornado.gen.Return(group)

    @tornado.gen.coroutine
    def create_user_group(self, group_name, functions):
        yield self.insert_object('user_group', data = {"func_name" : group_name, "functions" : functions, "func_type" : "function_group"}, group_name = group_name)

    @tornado.gen.coroutine
    def get_user_salt_functions(self, username):
        user = yield self.find_user(username)
        salt_functions = [x for x in user.get('functions', []) if x.get('func_type', '') == 'salt']

        raise tornado.gen.Return(salt_functions)