from pprint import PrettyPrinter
import argparse, json
from va_api import APIManager


def get_mapping_arguments(providers_mapping, command):
    for key in command: 
        if key not in providers_mapping.keys():
            expected_keys = [x if x != 'kwargs' else '<End of command>'  for x in providers_mapping.keys()] 
            raise Exception('Invalid command: ' + ' '.join(command) + '; Failed at ' + key + '. Did not find it in expected keys : ' + str(expected_keys))

        providers_mapping = providers_mapping[key]
    #We have iterated throughout the entire command. If providers_mapping does not contain "kwargs", we are not at the bottom of the tree. 
    if 'kwargs' not in providers_mapping.keys():
        raise Exception('Invalid command: ' + ' '.join(command) + '; Parsed the entire command but did not find a suitable function. Maybe add one of these keywords : ' + str(providers_mapping.keys()))

    return providers_mapping['kwargs']


def call_function(user, password, endpoint, data = '{}', method = 'get'):
    if type(data) == str: 
        data = json.loads(data)
    print 'In call function with : ', user, password, endpoint, data, method
    api = APIManager(va_url='https://127.0.0.1:443', va_user=user, va_pass=password, verify=False)
    return api.api_call(endpoint, data = data, method = method)

def call_function_with_mapping(user, password, mapping, command):
    kwargs = get_mapping_arguments(mapping, command)
    kwargs['user'] = user
    kwargs['password'] = password

    return call_function(**kwargs)

def providers_function(user, password, command):
    providers_mapping = {
        'list' : {"kwargs" : {"endpoint" : "/providers", "data" : '{}'}},
    }
    return call_function_with_mapping(user, password, providers_mapping, command)

def apps_function(user, password, command):
    apps_mapping = {
        'list' : {
            'running' : {"kwargs" : {'endpoint' : '/providers/info', 'data' : '{}', 'method' : 'post'}}, 
            'available' : {"kwargs" : {'endpoint' : '/providers/info', 'data' : '{}', 'method' : 'post'}}, 
        }, 
        'directory' : {
            'users' : {
                'list' : {"kwargs" : {'endpoint' : '/panels/action', 'data' : {'server_name' : 'va-directory', 'action' : 'list_users'}}}, 
                'locked' : {"kwargs" : {'endpoint' : '/panels/action', 'data' : {'server_name' : 'va-directory', 'action' : 'list_users'}}},
            }
        }
    }
    return call_function_with_mapping(user, password, apps_mapping, command)

def services_function(user, password, command):
    services_mapping = {
        'list' : {
            'kwargs' : {"endpoint" : '/services'}, 
            'ok' : {"kwargs" : {'endpoint' : '/services/by_status', 'data' : '{"status" : "OK"}'}},
            'critical' : {"kwargs" : {'endpoint' : '/services/by_status', 'data' : '{"status" : "CRITICAL"}'}},
        }
    }
    return call_function_with_mapping(user, password, services_mapping, command)

def vpn_function(user, password, command):
    vpn_mapping = {
        'list' : {"kwargs" : {"endpoint" : '/apps/vpn_users'}}, 
        'status' : {"kwargs" :  {"endpoint" : '/apps/vpn_status'}},
        'add' : {"kwargs" : {'endpoint' : '/apps/add_vpn_user', 'data' : {"username" : "nekoj_username"}, 'method' : 'post'}}, 
        'get-cert' : {"kwargs" : {'endpoint' : '/apps/download_vpn_cert', 'data' : {"nekoj_username"}, 'method' : 'post'}},
    }
    return call_function_with_mapping(user, password, vpn_mapping, command)

def prepare_request_args(sub_parsers):
    api_request = sub_parsers.add_parser('request', description = 'Performs an api call on the va_master. ')
    api_request.set_defaults(sub = 'api_request')

    api_request.add_argument('--endpoint', help = 'The endpoint for the request. ')
    api_request.add_argument('--method', help = 'The method to use. Default is GET. ', default = 'get')
    api_request.add_argument('--data', help= 'The data to send to the request. Must be properly formed JSON. Default: \'{}\'', default = '{}')

def prepare_providers_args(sub_parsers):
    providers = sub_parsers.add_parser('providers', description = 'Allows you to call various providers related functions. ')
    providers.set_defaults(sub = 'providers')

    providers.add_argument('command', nargs = '*', choices = ['list', 'add', 'nesho'], help = 'Specific provider command. TODO document this. ')

def prepare_apps_args(sub_parsers):
    apps = sub_parsers.add_parser('apps', description = 'Allows you to call various apps related functions. ')
    apps.set_defaults(sub = 'apps')

    apps.add_argument('command', nargs = '*', choices = ['list', 'running', 'available', 'directory', 'users', 'all', 'locked'])

def prepare_services_args(sub_parsers):
    services = sub_parsers.add_parser('services', description = 'Allows you to call various services related functions. ')
    services.set_defaults(sub = 'services')

    services.add_argument('command', nargs = '*', choices = ['list', 'ok', 'critical'])

def prepare_vpn_args(sub_parsers):
    vpn = sub_parsers.add_parser('vpn')
    vpn.set_defaults(sub = 'vpn')

    vpn.add_argument('command', nargs = '*', choices = ['list', 'status', 'add', 'get-cert'])

def main():
    parser = argparse.ArgumentParser(description = 'VA client argument parse. ')
    parser.add_argument('--user', help = 'The username with which to make the request. ')
    parser.add_argument('--password', help = 'The password with which to authenticate the request. ')

    sub_parsers = parser.add_subparsers()

    prepare_request_args(sub_parsers)
    prepare_providers_args(sub_parsers)
    prepare_apps_args(sub_parsers)
    prepare_services_args(sub_parsers)
    prepare_vpn_args(sub_parsers)

    args = parser.parse_args()
    kwargs = vars(args)
    kwargs = {x : kwargs[x] for x in kwargs if x[0] != '_' and x not in ['sub']}

    functions = {
        'api_request' : call_function,
        'providers' : providers_function,
        'apps' : apps_function, 
        'services' : services_function,
    }

    result = functions[args.sub](**kwargs)
    pprinter = PrettyPrinter(indent = 4)
    pprinter.pprint(result)
#    print result

main()
