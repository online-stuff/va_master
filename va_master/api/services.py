import requests, json, subprocess

import tornado.gen

consul_url = 'http://localhost:8500/v1'
consul_dir = '/etc/consul.d'

def get_paths():
    paths = {
        'get' : {
            'services' : {'function' : list_services, 'args' : []},
            'services/by_status' : {'function' : get_services_with_status, 'args' : ['status']},
            'services/by_service' : {'function' : get_service, 'args' : ['service']},

        },
        'post' : {
            'services/add' : {'function' : add_services, 'args' : ['services', 'server']},
        },
        'delete' : {
            'services/delete' : {'function' : delete_services, 'args' : ['server']},
        }
    }
    return paths

def reload_systemctl():
    subprocess.check_output(['systemctl', 'daemon-reload'])

def restart_consul():
    subprocess.check_output(['consul', 'reload'])

@tornado.gen.coroutine
def list_services(deploy_handler):
    services = requests.get(consul_url + '/catalog/services')
    services = services.json()

    raise tornado.gen.Return(services)

@tornado.gen.coroutine
def get_services_with_status(deploy_handler, status = 'passing'):
    services = requests.get(consul_url + '/health/state/%s' % (status))
    services = services.json()

    raise tornado.gen.Return(services)

@tornado.gen.coroutine
def get_service(deploy_handler, service):
    service = requests.get(consul_url + '/health/checks/%s' % (service))
    service = service.json()

    raise tornado.gen.Return(service)

#Example for how to add services: 
#{"services": [{"name": "va-os", "tags": ["hostsvc", "web", "http"], "address": "192.168.80.16", "port": 5000, "check": {"id": "tcp", "name": "TCP connection to port", "tcp": "192.168.80.16:5000", "interval": "30s", "timeout": "10s"}}, {"name": "imconfus", "tags": ["hostsvc", "web", "http"], "address": "192.168.80.16", "port": 5000, "check": {"id": "tcp", "name": "TCP connection to port", "tcp": "192.168.80.16:5000", "interval": "30s", "timeout": "10s"}}]}


@tornado.gen.coroutine
def create_service_from_state(deploy_handler, state_name, service_name, service_address, service_port, server_name):
    all_states = yield deploy_handler.get_states()
    state = [x for x in all_states if x['name'] == state_name][0]

    state_service = state['service']
    services = state_service['services']
    for service in services: 
        for check in services[service]:
            for k in services[service][k]:
                if 'VAR_' in services[service][k]:
                    #Somehow do work with var
                    pass

    yield add_service_with_definition(deploy_handler, service_definition, server_name)

@tornado.gen.coroutine
def add_service_with_definition(deploy_handler, service_definition, server):
    service_text = json.dumps(service_definition)
    service_conf = consul_dir + '/%s.json' % server

    with open(service_conf, 'w') as f:
        f.write(service_text)

    reload_systemctl()
    restart_consul()

@tornado.gen.coroutine
def add_services(deploy_handler, services, server):
    service_keys = ['name', 'tags', 'address', 'port', 'check']
    for key in service_keys:
        if not all([x.get(key) for x in services]):
            raise tornado.gen.Return({"success" : False, "message" : "All services need to define a value for the keys: " + ', '.join(service_keys) + '; Missing key : ' + key, 'data' : {}})

    yield add_service_with_definition(deploy_handler, services, server)


@tornado.gen.coroutine
def add_services_presets(deploy_handler, minion_info, presets):
    check_presets = {
        "tcp" :  {"id": minion_info['id'] + "_tcp", "name": "Check server TCP", "tcp": minion_info['ip4_interfaces']['eth0'][0], "interval": "30s", "timeout": "10s"}, 
        "ping" :  {"id": minion_info['id'] + "_ping", "name": "Ping server", "script" : "ping -c1 " + minion_info['ip4_interfaces']['eth0'][0] + " > /dev/null", "interval": "30s", "timeout": "10s"}, 

    }
    service = {"service": {"name": minion_info["id"] + "_services", "tags": ["hostsvc", "web", "http"], "address": minion_info['ip4_interfaces']['eth0'][0], "port": 443, "checks" : [ 
        check_presets[p] for p in presets
    ]}}
    yield add_service_with_definition(deploy_handler, service, minion_info['id'])

@tornado.gen.coroutine
def delete_services(deploy_handler, server):
    service_conf = consul_dir + '/%s.json' % server
    os.remove(service_conf)

    reload_systemctl()
    restart_consul()
