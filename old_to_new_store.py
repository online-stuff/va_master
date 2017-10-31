import requests, json, functools
import base64
path = 'http://127.0.0.1:8500'

from va_master.datastore_handler import DatastoreHandler
from va_master.datastore import ConsulStore

import tornado.ioloop

datastore = ConsulStore()
datastore_handler = DatastoreHandler(datastore, '/opt/va_master/consul_spec.json')

run_sync = tornado.ioloop.IOLoop.instance().run_sync

def datastore_get(handle, get_key = ''):
    url = '%s/v1/kv/%s' % (path, handle)
    print 'Url is : ', url
    result = requests.get(url).text
    result = json.loads(result)
    result = [x['Value'] for x in result]
    result = [json.loads(base64.b64decode(x)) for x in result]
    result = result[0]
    if get_key: 
        result = result.get(get_key, result)
    return result

def datastore_insert(handle, data):
    url = '%s/v1/kv/%s' % (path, handle)
    print 'Url is : ', url
    result = requests.put(url, data = data)
    print result

def old_to_new_datastore(object_name, object_handle_unformatted, object_handle_ids = [], get_key = '', special_data_parsing = None, special_data_kwargs = {}, old_key = ''):
    print 'In func'
    if not old_key:
        old_key = object_name + 's'
    old_data = datastore_get(old_key, get_key)
    print 'Old data is : ', old_data
    for data in old_data:
        handles = {x : data.get(x) for x in object_handle_ids}
        object_handle = object_handle_unformatted.format(**handles)

        if special_data_parsing: 
            data = special_data_parsing(data, **special_data_kwargs)

        print 'Want to insert : ', data, ' in : ', object_handle, ' with handles : ', handles
        run_sync(functools.partial(datastore_handler.insert_object, object_name, data = data, handle_data = handles))

def panel_parsing(data, user_type):
    if type(data['panels']) == list: 
        data['panels'] = {user_type : []}
    panel = {
        'name' : data['name'], 
        'panels' : data['panels'][user_type], 
        'icon' : data['icon'], 
        'servers' : data['servers']
    }
    return panel

def convert_all():
    print 'Converting!'
    print old_to_new_datastore('provider', 'providers/{provider_name}', ['provider_name'])
    old_to_new_datastore('user', 'users/{username}', ['username'])
    old_to_new_datastore('admin', 'admins/{username}', ['username'])
    old_to_new_datastore('admin_panel', 'panels/admin/{name}', ['name'], get_key = 'admin', special_data_parsing = panel_parsing, special_data_kwargs = {"user_type" : "admin"}, old_key = 'panels')
    old_to_new_datastore('user_panel', 'panels/user/{name}', ['name'], get_key = 'user', special_data_parsing = panel_parsing, special_data_kwargs = {"user_type" : "user"}, old_key = 'panels')
    old_to_new_datastore('user_group', 'user_groups/{group_name}', ['group_name'])
    old_to_new_datastore('state', 'state/{name}', ['name'], get_key = 'states', old_key = 'init_vals')


 
if __name__ == '__main__' : 
    convert_all() 
