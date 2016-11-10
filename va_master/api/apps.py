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
def get_state(state):
    #TODO see if request was successful
    result = requests.get(base_repo_link + links_to_states[state])
    return result.text

@auth_only
@tornado.gen.coroutine
def launch_app(handler):
    data = json.loads(handler.request.body)
    deploy_handler = handler.config.deploy_handler
    store = deploy_handler.datastore

    hosts = yield store.get('hosts')
    required_host = [host for host in hosts if host['hostname'] == data['hostname']][0]
    driver = yield deploy_handler.get_driver_by_id(required_host['driver_name'])
    print ('Driver is : ', driver, ' with id : ', required_host['driver_name'])
    tornado.gen.Return(None)

    try: 
        profile_dir = required_host['profile_conf_dir']
        profile_template = ''

        with open(profile_dir) as f: 
            profile_template = f.read()


        driver.profile_vars['VAR_ROLE'] = data['role']
        new_profile = data['minion_name'] + '-profile'
        driver.profile_vars['VAR_PROFILE_NAME'] = new_profile
        driver.profile_template = profile_template

        yield driver.get_salt_configs(skip_provider = True)
        yield driver.write_configs(skip_provider = True)
    except Exception as e: 
        print(e)
    

    #probably use salt.cloud somehow, but the documentation is terrible. 
    new_minion_cmd = ['salt-cloud', '-p', new_profile, data['minion_name']]
    minion_apply_state = ['salt', data['minion_name'], 'state.highstate']

    subprocess.call(new_minion_cmd)

#    state_file = yield get_state(state)
#    with open('/srv/salt' + links_to_states[state], 'w') as f: 
#        f.write(state_file)

    subprocess.call(minion_apply_state)
