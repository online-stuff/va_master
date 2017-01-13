from .login import auth_only
import tornado.gen
import json
import subprocess
import requests
import zipfile, tarfile
from salt.client import Caller

from salt.client import Caller


@tornado.gen.coroutine
def add_app(handler):
    app = yield get_app_info(handler)
    yield handler.config.deploy_handler.store_app(app, handler.data['host'])

#@auth_only
def get_openvpn_users(handler):
    cl = Caller()
    users = cl.cmd('openvpn.list_users')
    users['active'] = [{'name' : x, 'check' : False, 'connected' : x in users['status']['client_list']} for x in users['active']]
    handler.json(users)

@tornado.gen.coroutine
def perform_instance_action(handler): 
    try: 
        data = handler.data
        store = handler.config.deploy_handler.datastore
        hosts = yield store.get('hosts')

        host = [x for x in hosts if x['hostname'] == data['hostname']][0]
        driver = yield handler.config.deploy_handler.get_driver_by_id(host['driver_name'])
        success = yield driver.instance_action(host, data['instance_name'], data['action'])
    except: 
        import traceback
        traceback.print_exc()


@tornado.gen.coroutine
def manage_states(handler, action = 'append'):
    try:
        deploy_handler = handler.config.deploy_handler
        current_states = yield deploy_handler.datastore.get('states')

        #TODO delete from /srv/salt
        getattr(current_states, action)(handler.data['name'])
        store_action = {
            'append' : deploy_handler.datastore.insert, 
            'delete' : deploy_handler.datastore.delete, 
        }[action]

        yield store_action('states', current_states)
        yield deploy_handler.generate_top_sls()
    except: 
        import traceback
        traceback.print_exc()

@tornado.gen.coroutine
def get_states(handler):
    states_data = yield handler.config.deploy_handler.get_states()
    handler.json(states_data)


@tornado.gen.coroutine
def reset_states(handler):
    yield handler.config.deploy_handler.reset_states()


@tornado.gen.coroutine
def create_new_state(handler):
    data = handler.data['file'][0]
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
    print ('Names are : ', tar_ref.getnames())

#    zip_ref.close()
    tar_ref.close()
    manage_states(handler, 'append')


@tornado.gen.coroutine
def get_app_info(handler):
    instance_name = handler.data['instance_name']
   
    cl = Caller()
    instance_info = cl.cmd('mine.get', instance_name, 'inventory') 

    raise tornado.gen.Return(instance_info)

        
#@auth_only
@tornado.gen.coroutine
def launch_app(handler):
    try: 
        data = handler.data
        print ('My data is : ', data)
        deploy_handler = handler.config.deploy_handler
        store = deploy_handler.datastore


        hosts = yield store.get('hosts')
        print (data)
        print (data['hostname'])
        required_host = [host for host in hosts if host['hostname'] == data['hostname']][0]

        driver = yield deploy_handler.get_driver_by_id(required_host['driver_name'])
        yield driver.create_minion(required_host, data)

        panel = yield deploy_handler.get_states_info()
        panel = [x for x in panel if x['name'] == data['role']][0]['panels']
        yield deploy_handler.store_panel(panel['panels'])
        


        minion_info = yield get_app_info(handler)

        states = yield store.get('states')
        state = [x for x in states if x['name'] == data['role']][0]

        required_host['instances'].append(minion_info)
        yield store.insert('hosts', hosts)
    except: 
        import traceback
        traceback.print_exc()

@tornado.gen.coroutine
def get_user_actions(handler):
    actions = yield handler.config.deploy_handler.get_actions(int(handler.data.get('no_actions', 0)))
    handler.json(actions)
