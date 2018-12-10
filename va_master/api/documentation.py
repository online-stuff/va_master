import tornado
import json, yaml, subprocess, importlib, inspect, socket

import salt.client
from salt.client import LocalClient 

def get_paths():
    paths = {
        'get' : {
            'panels/get_all_function_groups' : {'function' : get_all_function_groups, 'args' : ['datastore_handler']},
        },
        'post' : {
        }
    }
    return paths

def function_is_documented(doc):
    """
        description: Checks if a function is documented properly. In order for it to be so, it needs to have a __doc__ string which is yaml formatted, and it should be a dictionary with 'description', 'output' and 'arguments' keys, plus any others you want, where 'description' and 'output' are strings, and 'arguments' is a list of dictionaries where the key is the name of the argument, and the value is its description. 
        arguments: 
          - f: The function for whih the check is done
        output: Boolean, whether the function is formatted. 
        hide: True
        
    """

    #Sometimes we straight up pass the docstring to this function. 
    if callable(doc): 
        doc = doc.__doc__

    #Make sure doc is not empty
    if doc:
        #Check if doc is yaml
        try:
            doc = yaml.load(doc)
            #And dict
            if type(doc) == dict:
                #description should be string, arguments should be a list of dictionaries. 
                if type(doc['description']) == str and type(doc.get('arguments', [])) == list and all([type(x) == dict for x in doc.get('arguments', [])]):
                    #Finally, the function needs to actually be visible.
                    if doc.get('visible'): 
                        return True
        except yaml.parser.ParserError:
            pass
        except yaml.parser.ScannerError:
            pass
        except Exception: 
            print (doc)
            raise
    return False


def get_master_functions(handler):
    functions = {
        method : [
            [path, yaml.load(handler.paths[method][path]['function'].__doc__)] for path in handler.paths[method] if function_is_documented(handler.paths[method][path]['function'])
        ] for method in ['post', 'get']
    }
    return functions

def get_salt_functions():
    cl = LocalClient()

    salt_functions = cl.cmd('G@role:va-master', fun = 'va_utils.get_documented_module_functions', tgt_type = 'compound')
    salt_functions = salt_functions.items()[0][1]

    salt_functions = {
        method : [[function[0], yaml.load(function[1])] for function in salt_functions[method] if function_is_documented(function[1])]
    for method in salt_functions}

    return salt_functions   

def func_group_is_method(func_group):
    return func_group in ['get', 'post', 'put', 'delete']

def get_func_group(func_group):
    return 'core' if func_group_is_method(func_group) else func_group

def get_master_domain():
    return socket.getfqdn()

def generate_url_for_func(func_doc, func_group):
    func_endpoint = func_doc[0] if func_group_is_method(func_group) else 'panels/action' 
    master_domain = get_master_domain()
    url = 'https://{master_domain}/api/{func_endpoint}'.format(master_domain = master_domain, func_endpoint = func_endpoint)
    return url

def generate_example_input_for_func(func_doc):
    data = {}
    for argument in func_doc[1].get('arguments', []):
        if argument.get("example") and argument.get("name"):
            data[argument['name']] = argument['example']

    return data

def generate_example_cli_for_func(func_doc, func_group, dash_user):
    data = generate_example_input_for_func(func_doc)
    if not func_group_is_method(func_group): 
        data['server_name'] = 'va-server' #TODO get actual server_name somehow, or see how to get a server
        data['action'] = func_doc[0]

    method = func_group if func_group_is_method(func_group) else 'post'
    method = method.upper()

    cmd = ['curl', '-k', '-X', method, '-H', 'Authorization: ' + dash_user['token']]
    url = generate_url_for_func(func_doc, func_group)
    if func_group == 'get':
        url_params = '?' + '='.join(['&'.join(x) for x in data.items()])
        url += url_params
    else: 
        cmd += ['-H', 'Content-type: application/json', '-d', json.dumps(data)]

    cmd += [url]
    cmd = subprocess.list2cmdline(cmd)

    return cmd

def format_functions_for_dashboard(functions, dash_user):
    functions = [
        { 
                'label' : get_func_group(func_group), 
                'options' : [
                    {
                        'label' : func_doc[0], 
                        'value' : func_doc[0], 
                        'documentation' : func_doc[1],
                        'example_url' : generate_url_for_func(func_doc, func_group),
                        'example_data' : generate_example_input_for_func(func_doc),
                        'example_cli' : generate_example_cli_for_func(func_doc, func_group, dash_user),
                        'method' : func_group if func_group_is_method(func_group) else 'post',
                    }
                    for func_doc in functions[func_group]
                ] 
        } for func_group in functions]

    result = []
    for func_group in functions: 
        existing_group = [x for x in result if x['label'] == func_group['label']]
        if existing_group: 
            existing_group = existing_group[0]
            existing_group['options'] += func_group['options']
        else: 
            result.append(func_group)

    return result


@tornado.gen.coroutine
def get_api_functions(datastore_handler):
    apps = yield datastore_handler.datastore.get_recurse('apps/')
    all_functions = {}
    for app in apps:
        imported_module = importlib.import_module(app['module'])
        module_functions = inspect.getmembers(imported_module, inspect.isfunction)
        module_functions = [[x[0], yaml.load(x[1].__doc__)] for x in module_functions if function_is_documented(x[1])]
        all_functions[app['name']] = module_functions

    raise tornado.gen.Return(all_functions)


@tornado.gen.coroutine
def get_all_functions(handler, dash_user):
    """
        description: Returns all functions that should be visible to the user from the dashboard. This is done by determining which functions are documented properly. Check the function_is_defined() function for more information. 
        arguments: 
          - handler: Generic argument inserted by the api_handler. Provides various utilities and data from va_master. 
        output: "Data formatted so as to be displayed by the dashboard directly. The format is: [{'label' : 'method/module', 'options' : [{'label' : 'func_name', 'value' : 'func_name', 'description' : 'description', 'documentation' : 'documentation'}, ...]}, ...]"
        hide: True
    """

    functions = get_master_functions(handler)
    salt_functions = get_salt_functions()
    api_functions = yield get_api_functions(handler.datastore_handler)

    functions.update(salt_functions)
    functions.update(api_functions)

    functions = format_functions_for_dashboard(functions, dash_user)

    raise tornado.gen.Return(functions)


@tornado.gen.coroutine
def get_all_function_groups(datastore_handler):
    """Returns all user function groups from the datastore. """
    groups = yield datastore_handler.get_user_groups()
    print ('Groups are : ', groups)
    for g in groups:
        g['functions'] = [x.get('value') for x in g['functions']]
    raise tornado.gen.Return(groups)


