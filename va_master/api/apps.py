from .login import auth_only
import tornado.gen
import json
import subprocess

@auth_only
@tornado.gen.coroutine
def launch_app(handler):
    data = json.loads(handler.request.body)
    store = handler.config.deploy_handler.datastore
    hosts = yield store.get('hosts')
    required_host = [host for host in hosts if host['hostname'] == data['hostname']][0]

    #probably use salt.cloud somehow, but the documentation is terrible. 
    new_minion_cmd = ['salt-cloud', '-p', required_host['profile_conf'], data['minion_name']]
    minion_apply_state = ['salt', data['minion_name'], data['state'] + '.apply']

    subprocess.call(new_minion_cmd)
    subprocess.call(minion_apply_state)
