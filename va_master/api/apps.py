from .login import auth_only
import tornado.gen
import json
import subprocess
import requests



@tornado.gen.coroutine
def manage_states(handler, action = 'append'):
    try:
        deploy_handler = handler.config.deploy_handler
        current_states = yield deploy_handler.datastore.get('states')
        data = handler.data
        new_state = {
            'name' : data['name'],
            'version' : data['version'],
            'description' : data['description'], 
            'icon' : data['icon'], 
            'dependency' : data['dependency'], 
            'path' : data['path'],
            'substates' : data['substates']
        }
        getattr(current_states, action)(new_state)
        yield deploy_handler.datastore.insert('states', current_states)
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
    files_archive = handler.data['files_archive']
    #TODO maybe get it from config? 
    salt_path = '/srv/salt/'
    with open(salt_path + handler.data['state_name']) as f:
        f.write(files_archive)
    #unzip(file_archive)
    manage_states(handler, 'append')


@tornado.gen.coroutine
def get_app_info(handler):
    instance_name = handler.data['instance_name']
    
    instance_info_cmd = ['salt-call', instance_name, 'mine.get', 'inventory', '--output', 'json']
    instance_info = json.loads(subprocess.check_output(instance_info_cmd))

    raise tornado.gen.Return(get_app_info)

        
#@auth_only
@tornado.gen.coroutine
def launch_app(handler):
    try: 
        data = handler.data
        deploy_handler = handler.config.deploy_handler
        store = deploy_handler.datastore


        hosts = yield store.get('hosts')
        print (data)
        print (data['hostname'])
        required_host = [host for host in hosts if host['hostname'] == data['hostname']][0]

        driver = yield deploy_handler.get_driver_by_id(required_host['driver_name'])
        yield driver.create_minion(required_host, data)
        minion_info = yield get_app_info(handler)

        states = yield store.get('states')
        state = [x for x in states if x['name'] == data['role']][0]


        panels = yield store.get('panels')
        panels.append({'name' : data['instance_name'], 'role' : data['role'], 'user_allowed' : state.get('user_allowed', False)})

        required_host['instances'].append(data['instance_name'])
        yield store.insert('hosts', hosts)
    except: 
        import traceback
        traceback.print_exc()



