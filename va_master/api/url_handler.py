import tornado.ioloop

from . import *
import sys
import types

def imports():
    for name, val in globals().items():
        if isinstance(val, types.ModuleType):
            yield val


def gather_paths():
    paths = {'get' : {}, 'post' : {}, 'delete' : {}, 'put' : {}}
    user_allowed = []


    api_modules = [x for x in imports()]
    api_modules = [x for x in api_modules if getattr(x, 'get_paths', None)]

    for api_module in api_modules:
        module_paths = api_module.get_paths()
        for protocol in paths:
            paths[protocol].update(module_paths.get(protocol, {}))
        user_allowed += module_paths.get('user_allowed', [])
    
    paths['user_allowed'] = user_allowed
    return paths
