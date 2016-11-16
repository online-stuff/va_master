from .login import auth_only
import tornado.gen
import json
import subprocess
import requests

base_repo_link = 'https://raw.github.com/VapourApps/saltstack/master/states'
links_to_states = {
    'samba' : '/directory/directory.sls' , 
}


@tornado.gen.coroutine
def manage_states(handler, action = 'append'):
    current_states = deploy_handler.datastore.get('states')
    getattr(current_states, action)(handler.data['state_name'])
    deploy_handler.datastore.insert('states', current_states)
    handler.deploy_handler.generate_top_sls()


@tornado.gen.coroutine
def create_new_state(handler):
    files_archive = handler.data['files_archive']
    #TODO maybe get it from config? 
    salt_path = '/srv/salt/'
    with open(salt_path + handler.data['state_name']) as f:
        f.write(files_archive)
    #unzip(file_archive)
    manage_states(handler, 'append')
        


@tornado.gen.coroutine
def get_state(state):
    #TODO see if request was successful
    result = requests.get(base_repo_link + links_to_states[state])
    return result.text

@auth_only
@tornado.gen.coroutine
def launch_app(handler):
    data = handler.data
    deploy_handler = handler.deploy_handler
    store = deploy_handler.datastore

    hosts = yield store.get('hosts')
    required_host = [host for host in hosts if host['hostname'] == data['hostname']][0]
    driver = yield deploy_handler.get_driver_by_id(required_host['driver_name'])
    print ('Driver is : ', driver, ' with id : ', required_host['driver_name'])

    try: 
        yield deploy_handler.create_minion(driver, host)
    except: 
        import traceback
        traceback.print_exc()

