from .login import auth_only
import tornado.gen
import json
import subprocess
import requests


@tornado.gen.coroutine
def manage_states(handler, action = 'append'):
    yield current_states = deploy_handler.datastore.get('states')
    new_state = {
        'name' : data['state_name'],
        'description' : data['description'], 
        'version' : 'data['version'],
        'icon' : data['icon'], 
        'dependency' : data['dependency'], 
        'path' : data['path'],
    }
    getattr(current_states, action)(new_state)
    yield deploy_handler.datastore.insert('states', current_states)
    yield handler.deploy_handler.generate_top_sls()


@tornado.gen.coroutine
def get_states_data(handler):
    states_data = yield deploy_handler.datastore.get('states')
    raise tornado.gen.Return(states_data)

@tornado.gen.coroutine
def create_new_state(handler):
    files_archive = handler.data['files_archive']
    #TODO maybe get it from config? 
    salt_path = '/srv/salt/'
    with open(salt_path + handler.data['state_name']) as f:
        f.write(files_archive)
    #unzip(file_archive)
    manage_states(handler, 'append')
        
@auth_only
@tornado.gen.coroutine
def launch_app(handler):
    try: 
        data = handler.data
        deploy_handler = handler.config.deploy_handler
        store = deploy_handler.datastore


        hosts = yield store.get('hosts')
        required_host = [host for host in hosts if host['hostname'] == data['hostname']][0]

        data = {'role' : 'directory', 'minion_name' : 'nino_minion', 'fqdn' : 'nekoj.domen', 'image' : 'xenial-server-cloudimg-amd64-disk1.img', 'hostname' : data['hostname'], 'host_ip' : required_host['host_ip']}

        driver = yield deploy_handler.get_driver_by_id(required_host['driver_name'])
        yield driver.create_minion( host, data)
    except: 
        import traceback
        traceback.print_exc()

