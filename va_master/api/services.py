import requests, json, subprocess

import tornado.gen
from salt.client import LocalClient


consul_url = 'http://localhost:8500/v1'
consul_dir = '/etc/consul.d'

def get_paths():
    paths = {
        'get' : {
            'services' : {'function' : list_services, 'args' : []},
            'services/full_status' : {'function' : get_services_and_monitoring, 'args' : []},
            'services/by_status' : {'function' : get_services_with_status, 'args' : ['status']},
            'services/by_service' : {'function' : get_service, 'args' : ['service']},
            'services/get_monitoring_status' : {'function' : get_all_monitoring_data, 'args' : []},

        },
        'post' : {
            'services/add' : {'function' : add_services, 'args' : ['services', 'server']},
        },
        'delete' : {
            'services/delete' : {'function' : delete_services, 'args' : ['server']},
        }
    }
    return paths


#These two functions are for inside use in the API. 
def reload_systemctl():
    subprocess.check_output(['systemctl', 'daemon-reload'])

def restart_consul():
    subprocess.check_output(['consul', 'reload'])

@tornado.gen.coroutine
def get_services_and_monitoring():
    """Returns a list of all services as well as monitoring data from all connected monitoring minions. """
    services = yield list_services()
    result = yield get_all_monitoring_data()
    result.update(services)

    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def list_services():
    """Returns a list of services and their statuses from the consul REST API"""
    services = requests.get(consul_url + '/catalog/services')
    services = services.json()

    raise tornado.gen.Return(services)

@tornado.gen.coroutine
def get_services_with_status(status = 'passing'):
    """Returns a list of services with the specified status. """
    services = requests.get(consul_url + '/health/state/%s' % (status))
    services = services.json()

    raise tornado.gen.Return(services)

@tornado.gen.coroutine
def get_service(service):
    """Returns the service with the specified service name. """
    service = requests.get(consul_url + '/health/checks/%s' % (service))
    service = service.json()

    raise tornado.gen.Return(service)

#Example for how to add services: 
#{"services": [{"name": "va-os", "tags": ["hostsvc", "web", "http"], "address": "192.168.80.16", "port": 5000, "check": {"id": "tcp", "name": "TCP connection to port", "tcp": "192.168.80.16:5000", "interval": "30s", "timeout": "10s"}}, {"name": "imconfus", "tags": ["hostsvc", "web", "http"], "address": "192.168.80.16", "port": 5000, "check": {"id": "tcp", "name": "TCP connection to port", "tcp": "192.168.80.16:5000", "interval": "30s", "timeout": "10s"}}]}


@tornado.gen.coroutine
def create_service_from_state(state_name, service_name, service_address, service_port, server_name):
    """Creates a service from the specified state. Not used currently. """
    all_states = yield datastore_handler.get_states_data()
    state = [x for x in all_states if x['name'] == state_name][0]

    state_service = state['service']
    services = state_service['services']
    for service in services: 
        for check in services[service]:
            for k in services[service][k]:
                if 'VAR_' in services[service][k]:
                    #Somehow do work with var
                    pass

    yield add_service_with_definition(service_definition, server_name)

@tornado.gen.coroutine
def add_service_with_definition(service_definition, server):
    """Adds a service with a definition. The definition has the standard consul service format. """
    service_text = json.dumps(service_definition)
    service_conf = consul_dir + '/%s.json' % server

    with open(service_conf, 'w') as f:
        f.write(service_text)

    reload_systemctl()
    restart_consul()

@tornado.gen.coroutine
def add_services(services, server):
    service_keys = ['name', 'tags', 'address', 'port', 'check']
    for key in service_keys:
        if not all([x.get(key) for x in services]):
            raise tornado.gen.Return({"success" : False, "message" : "All services need to define a value for the keys: " + ', '.join(service_keys) + '; Missing key : ' + key, 'data' : {}})

    yield add_service_with_definition(deploy_handler, services, server)


@tornado.gen.coroutine
def add_services_presets(minion_info, presets):
    """Creates services based on several presets and the info for the server. The info is required to get the id and the IP of the server. """
    check_presets = {
        "tcp" :  {"id": minion_info['id'] + "_tcp", "name": "Check server TCP", "tcp": minion_info['ip4_interfaces']['eth0'][0], "interval": "30s", "timeout": "10s"}, 
        "ping" :  {"id": minion_info['id'] + "_ping", "name": "Ping server", "script" : "ping -c1 " + minion_info['ip4_interfaces']['eth0'][0] + " > /dev/null", "interval": "30s", "timeout": "10s"}, 

    }
    service = {"service": {"name": minion_info["id"] + "_services", "tags": ["hostsvc", "web", "http"], "address": minion_info['ip4_interfaces']['eth0'][0], "port": 443, "checks" : [ 
        check_presets[p] for p in presets
    ]}}
    yield add_service_with_definition(service, minion_info['id'])


@tornado.gen.coroutine
def delete_services(server):
    """Deletes all services for a server. """
    service_conf = consul_dir + '/%s.json' % server
    os.remove(service_conf)

    reload_systemctl()
    restart_consul()

@tornado.gen.coroutine
def get_all_monitoring_data():
    """Returns all icinga data from connected monitoring minions. """
    cl = LocalClient()
    result = cl.cmd('G@role:monitoring', fun = 'monitoring.icinga2', tgt_type = 'compound')

    return result
