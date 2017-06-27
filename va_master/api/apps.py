from .login import auth_only
import tornado.gen
import json
import subprocess
import requests
import zipfile, tarfile

from salt.client import Caller, LocalClient

import panels

def get_paths():
    paths = {
        'get' : {
            'apps/vpn_users' : {'function' : get_openvpn_users, 'args' : []},
            'apps/vpn_status' : {'function' : get_openvpn_status, 'args' : []},
            'apps/add_app' : {'function' : add_app, 'args' : ['host']},
            'apps/get_actions' : {'function' : get_user_actions, 'args' : []},

            'states' : {'function' : get_states, 'args' : []},
            'states/reset' : {'function' : reset_states, 'args' : []},#Just for testing


        },
        'post' : {
            'state/add' : {'function' : create_new_state,'args' : ['file', 'body', 'filename']},

            'apps' : {'function' : launch_app, 'args' : ['role', 'hostname', 'instance_name', 'role', 'image', 'size', 'network']},
            'apps/action' : {'function' : perform_instance_action, 'args' : ['hostname', 'action', 'instance_name']},
            'apps/add_vpn_user': {'function' : add_openvpn_user, 'args' : ['username']},
            'apps/revoke_vpn_user': {'function' : revoke_openvpn_user, 'args' : ['username']},
            'apps/list_user_logins': {'function' : list_user_logins, 'args' : ['username']},
            'apps/download_vpn_cert': {'function' : download_vpn_cert, 'args' : ['username']},
        }
    }
    return paths

@tornado.gen.coroutine
def add_app(deploy_handler):
    app = yield get_app_info(deploy_handler)
    yield handler.config.deploy_handler.store_app(app, handler.data['host'])

@tornado.gen.coroutine
def get_openvpn_users(deploy_handler):
    cl = Caller()
    users = cl.cmd('openvpn.list_users')
    users['active'] = [{'name' : x, 'check' : False, 'connected' : x in users['status']['client_list']} for x in users['active']]
    users['status'] = users['status']['client_list']
    raise tornado.gen.Return(users)

@tornado.gen.coroutine
def get_openvpn_status(deploy_handler):
    cl = Caller()
    status = cl.cmd('openvpn.get_status')
    raise tornado.gen.Return(status)

@tornado.gen.coroutine
def add_openvpn_user(deploy_handler, username):
    cl = Caller()
    success = cl.cmd('openvpn.add_user', username = username)
    raise tornado.gen.Return(success)

@tornado.gen.coroutine
def revoke_openvpn_user(deploy_handler, username):
    cl = Caller()
    success = cl.cmd('openvpn.revoke_user', username = username)
    raise tornado.gen.Return(success)   

@tornado.gen.coroutine
def list_user_logins(deploy_handler, username): 
    cl = Caller()
    success = cl.cmd('openvpn.list_user_logins', user = username)
    raise tornado.gen.Return(success)

@tornado.gen.coroutine
def download_vpn_cert(deploy_handler, username):
    cl = Caller()
    cert = cl.cmd('openvpn.get_config', username = username)

    vpn_cert_path = '/tmp/' + username + '_vpn.cert'
    with open(vpn_cert_path, 'w') as f: 
        f.write(cert)
 
    handler.serve_file(vpn_cert_path)
    raise tornado.gen.Return({'data_type' : 'file'})


@tornado.gen.coroutine
def perform_instance_action(deploy_handler, hostname, action, instance_name): 
    try: 
        store = deploy_handler.datastore
        hosts = yield store.get('hosts')

        host = [x for x in hosts if x['hostname'] == hostname][0]
        driver = yield handler.config.deploy_handler.get_driver_by_id(host['driver_name'])
        success = yield driver.instance_action(host, instance_name, action)
    except: 
        import traceback
        traceback.print_exc()


@tornado.gen.coroutine
def manage_states(deploy_handler, name, action = 'append'):
    try:
        current_states = yield deploy_handler.datastore.get('states')

        #TODO delete from /srv/salt
        getattr(current_states, action)(name)
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
def get_states(deploy_handler):
    states_data = yield deploy_handler.get_states()
    raise tornado.gen.Return(states_data)


@tornado.gen.coroutine
def reset_states(deploy_handler):
    yield handler.config.deploy_handler.reset_states()


@tornado.gen.coroutine
def create_new_state(deploy_handler, file_contents, body, filename):
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
    manage_states(handler, 'append')


@tornado.gen.coroutine
def get_app_info(deploy_handler, instance_name):
    cl = Caller()
    print ('Getting inventory for :', instance_name)
    instance_info = cl.cmd('mine.get', instance_name, 'inventory') 
    print ('Info is : ', instance_info)
    raise tornado.gen.Return(instance_info)

        
##@auth_only
@tornado.gen.coroutine
def launch_app(deploy_handler):
    data = handler.data
    store = deploy_handler.datastore


    hosts = yield store.get('hosts')
    required_host = [host for host in hosts if host['hostname'] == data['hostname']][0]

    driver = yield deploy_handler.get_driver_by_id(required_host['driver_name'])
    result = yield driver.create_minion(required_host, data)

    minion_info = yield get_app_info(deploy_handler)

    if data.get('role'):

        init_vals = yield store.get('init_vals')
        states = init_vals['states']
        state = [x for x in states if x['name'] == data['role']][0]

        panel = {'panel_name' : handler.data['instance_name'], 'role' : minion_info['role']}
        panel.update(state['panels'])
        yield handler.config.deploy_handler.store_panel(panel)

    required_host['instances'].append(minion_info)
    yield store.insert('hosts', hosts)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def get_user_actions(deploy_handler):
    actions = yield deploy_handler.get_actions(int(handler.data.get('no_actions', 0)))
    raise tornado.gen.Return(actions)
