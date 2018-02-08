import requests, json, subprocess

import tornado.gen
from salt.client import LocalClient
import apps

consul_url = 'http://localhost:8500/v1'
consul_dir = '/etc/consul.d'

def get_paths():
    paths = {
        'get' : {
            'get_va_master_version' : {'function' : get_version, 'args' : ['handler']},

            'services' : {'function' : list_services, 'args' : []},
            'services/full_status' : {'function' : get_services_and_monitoring, 'args' : []},
            'services/by_status' : {'function' : get_services_with_status, 'args' : ['status']},
            'services/by_service' : {'function' : get_service, 'args' : ['service']},
            'services/get_monitoring_status' : {'function' : get_all_monitoring_data, 'args' : ['datastore_handler']},
            'services/get_services_table_data' : {'function' : get_services_table_data, 'args' : []},
            'services/get_services_with_checks' : {'function' : get_all_checks, 'args' : []},
        },
        'post' : {
            'services/add' : {'function' : add_services, 'args' : ['services', 'server']},
            'services/add_preset' : {'function' : add_services_presets, 'args' : ['service_presets', 'server']},

        },
        'delete' : {
            'services/delete' : {'function' : delete_services, 'args' : ['server']},
        }
    }
    return paths

@tornado.gen.coroutine
def get_service_definition(service_name):
    service_path = '/etc/consul.d/%s.json' % (service_name)
    with open(service_path) as f: 
        service_definition = json.load(f)

    service_definition = service_definition.get('service', service_definition)

    raise tornado.gen.Return(service_definition)

@tornado.gen.coroutine
def get_all_service_definitions():
    services = yield list_services()
    services = services.keys()
    definitions = yield [get_service_definition(x) for x in services]
    print ('Definitions at beginning ', definitions)
#    definitions = [{"name" : x, "definition" : services[x]} for x in services]
    raise tornado.gen.Return(definitions)

@tornado.gen.coroutine
def get_services_table_data():
    definitions = yield get_all_service_definitions()
    checks = yield get_all_checks()

    services = [x for x in definitions if x.get('name') != 'consul' and x.get('name')]

    for service in services: 
        check_results = [checks[x] for x in checks if x == service['name']][0]
        for i in range(len(service['checks'])):
            service['checks'][i].update(check_results[i])

    services_table = [{
        'name' : s['name'], 
        'address' : s['address'], 
        'port' : s['port'], 
        'check' : [{'interval' : c.get('interval'), 'name' : c['id'], 'status' : c['Status'], 'output' : c.get('Output')} for c in s['checks']],
        'tags' : s['tags'], 
    } for s in services]

    raise tornado.gen.Return(services_table)

@tornado.gen.coroutine
def get_version(handler):
    version = handler.config.pretty_version()

    raise tornado.gen.Return(version)

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
    try:
        services_url = consul_url + '/catalog/services'
        services = requests.get(services_url)
        services = services.json()
    except: 
        import traceback
        print ('Error when getting services with %s' % (services_url))
        traceback.print_exc()
        raise Exception('There was an error attempting to list consul services. ')

    raise tornado.gen.Return(services)

@tornado.gen.coroutine
def get_all_checks():
    services = yield list_services()
    all_checks = yield {x : get_service(x) for x in services.keys()}
    raise tornado.gen.Return(all_checks)

@tornado.gen.coroutine
def get_services_with_status(status = 'passing'):
    """Returns a list of services with the specified status. """
    try:
        status_url = consul_url + '/health/state/%s' % (status)
        services = requests.get(status_url)
        services = services.json()
    except: 
        import traceback
        print ('Error when trying to get all services with status %s with url %s. ' % (status, status_url))
        traceback.print_exc()
        raise Exception('There was an error trying to get all services with status %s. ' % (status))

    raise tornado.gen.Return(services)

@tornado.gen.coroutine
def get_service(service):
    """Returns the service with the specified service name. """
    try:
        service_url = consul_url + '/health/checks/%s' % (service)
        service = requests.get(service_url)
        service = service.json()
    except: 
        import traceback
        print ('Error trying to get data for service %s with url %s. ' % (status, service_url))
        traceback.print_exc()
        raise Exception('There was an error getting data for the service %s. ' % (service))

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

#TODO check if the definition is alright, raise exception if not. 
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

    yield add_service_with_definition(services, server)


@tornado.gen.coroutine
def add_services_presets(server, service_presets):
    """Creates services based on several presets and the info for the server. The info is required to get the id and the IP of the server. """

    if type(server) == unicode: 
        minion_info = yield apps.get_app_info(server)
        print ('Minion is : ', minion_info)
   
    print ("server is : ", type(server))
    check_presets = {
        "tcp" :  {"id": minion_info['id'] + "_tcp", "name": "Check server TCP", "tcp": minion_info['ip4_interfaces']['eth0'][0], "interval": "30s", "timeout": "10s"}, 
        "ping" :  {"id": minion_info['id'] + "_ping", "name": "Ping server", "script" : "ping -c1 " + minion_info['ip4_interfaces']['eth0'][0] + " > /dev/null", "interval": "30s", "timeout": "10s"}, 
        "highstate" : {"id" : minion_info['id'] + '_highstate', "name" : "Check highstate", "script" : "salt " + minion_info['id'] + "state.highstate test=True | perl -lne 's/^Failed:\s+// or next; s/\s.*//; print'"}, 
    }


    unknown_presets = [p for p in check_presets if p not in check_presets.keys()]
    if unknown_presets:
        raise Exception('Presets %s not found in the list of available presets: %s' % (str(unknown_presets), str(check_presets.keys())))

    service = {"service": {"name": minion_info["id"] + "_services", "tags": ["hostsvc", "web", "http"], "address": minion_info['ip4_interfaces']['eth0'][0], "port": 443, "checks" : [ 
        check_presets[p] for p in check_presets
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
def get_all_monitoring_data(datastore_handler):
    """Returns all icinga data from connected monitoring minions. """
    cl = LocalClient()
    result = cl.cmd('G@role:monitoring', fun = 'va_monitoring.icinga2', tgt_type = 'compound')
    monitoring_errors = []

    for minion in result: 
        if type(result[minion]) == str:
            print ('Error getting monitoring data for %s, salt returned %s, but will go on as usual. ' % (minion, result[minion]))
            monitoring_errors.append(minion)
            continue
        for host in result[minion]: 
            if 'va_master' in host['host_name']: 
                panel = {'icon' : 'fa-circle'}
            else: 
                panel = yield datastore_handler.find_panel_for_server(host['host_name'])
            host['icon'] = panel['icon']

    if monitoring_errors: 
        monitoring_errors = 'There was an error with the monitoring server(s): ' + ', '.join(monitoring_errors)
        result = {'success' : True, 'data' : result, 'message' : monitoring_errors}
    raise tornado.gen.Return(result)
