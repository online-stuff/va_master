import json, glob, yaml, datetime
import requests
import subprocess
import traceback
import tornado
import tornado.gen

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
        print ('Handle data : ', handle_data)
        print ('ANd spec if : ', new_object_spec)
        new_object_handle = new_object_spec['consul_handle'].format(**handle_data)

        #TODO check data to be as designed in the spec
        new_object = data

        yield self.datastore.insert(new_object_handle, new_object)

    @tornado.gen.coroutine
    def get_object(self, object_type, **handle_data):
        object_spec = self.spec[object_type]
        object_handle = object_spec['consul_handle'].format(**handle_data)
        result = yield self.datastore.get(object_handle)

    @tornado.gen.coroutine
    def get_provider(self, provider_name):
        provider = yield self.get_object('provider', provider_name = provider_name)
        raise tornado.gen.Return(provider)

    @tornado.gen.coroutine
    def get_provider_and_driver(self, provider_name):
        provider = yield self.get_provider(provider_name)
        driver = provider['driver_id']

    @tornado.gen.coroutine
    def list_providers(self):
        providers = yield self.datastore.get_recurse('providers/')
        print ('In list : ', providers)
        raise tornado.gen.Return(providers)

    @tornado.gen.coroutine
    def get_triggers(self, provider_name):
        provider = yield self.get_provider(provider_name) 
        raise tornado.gen.Return(provider.get('triggers', []))

    @tornado.gen.coroutine
    def create_provider(self, field_values):
        yield self.insert_object('provider', data = field_values, provider_name = field_values['provider_name'])

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
        users = yield self.datastore.get(user_type)
        users = [x['username'] for x in users]
        raise tornado.gen.Return(users)


    @tornado.gen.coroutine
    def add_user_functions(self, user, functions):
        all_funcs = yield self.datastore.get('users_functions')

        user_funcs = all_funcs.get(user, [])
        user_funcs += functions
        
        all_funcs[user] = user_funcs

        yield self.datastore.insert('users_functions', all_funcs)

    @tornado.gen.coroutine
    def remove_user_functions(self, user, functions):
        all_funcs = yield seflf.datastore.get('users_functions')

        user_funcs = all_funcs.get(user, [])
        user_funcs = [x for x in user_funcs for y in functions if x.get('func_path') != y.get('func_path', '') or x.get('func_name') != y.get('func_name') ]

        all_funcs[user] = user_funcs

        yield self.datastore.insert('users_functions', all_funcs)


    @tornado.gen.coroutine
    def get_user_functions(self, user, func_type = ''):
        if not user: 
            raise tornado.gen.Return([])
        all_functions = yield self.datastore.get('users_functions')
        user_funcs = all_functions.get(user, [])

        user_group_functions = [x['functions'] for x in user_funcs if x.get('func_type', '') == 'function_group']

        user_funcs = [
            x.get('func_path') for x in user_funcs + user_group_functions 
        if x.get('func_type', '') == func_type and x.get('func_path')]

        raise tornado.gen.Return(user_funcs)
