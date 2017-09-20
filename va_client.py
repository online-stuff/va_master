from pprint import PrettyPrinter
import argparse, json
from va_api import APIManager

from va_client_utils import module_mappings, module_args, get_mapping_arguments


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

def prepare_request_args(sub_parsers):
    api_request = sub_parsers.add_parser('request', description = 'Performs an api call on the va_master. ')
    api_request.set_defaults(sub = 'api_request')

    api_request.add_argument('--endpoint', help = 'The endpoint for the request. ')
    api_request.add_argument('--method', help = 'The method to use. Default is GET. ', default = 'get')
    api_request.add_argument('--data', help= 'The data to send to the request. Must be properly formed JSON. Default: \'{}\'', default = '{}')

def main():
    parser = argparse.ArgumentParser(description = 'VA client argument parse. ')
    parser.add_argument('--user', help = 'The username with which to make the request. ')
    parser.add_argument('--password', help = 'The password with which to authenticate the request. ')

    sub_parsers = parser.add_subparsers()
    prepare_request_args(sub_parsers)

    for module in module_args: 
        m = sub_parsers.add_parser(module, description = module_args[module].get('description', ''))
        m.set_defaults(sub = module)

        m.add_argument('command', nargs = '*', choices = module_args[module]['choices'], help = module_args[module].get('help', ''))

    args = parser.parse_args()
    kwargs = vars(args)
    kwargs = {x : kwargs[x] for x in kwargs if x[0] != '_' and x not in ['sub']}

    if args.sub == 'api_request' : 
        result = call_function(**kwargs)
    else: 
        mapping = module_mappings[args.sub]
        kwargs['mapping'] = mapping
        result = call_function_with_mapping(**kwargs)

    pprinter = PrettyPrinter(indent = 4)
    pprinter.pprint(result)

main()
