import tornado.ioloop

from . import *
import sys
import types

def get_modules():
    for name, val in globals().items():
        if isinstance(val, types.ModuleType) and hasattr(val, 'get_paths'):
            yield val


def gather_paths():
    paths = {'get' : {}, 'post' : {}, 'delete' : {}, 'put' : {}}
    user_allowed = []

    for api_module in get_modules():
        module_paths = api_module.get_paths()
        for protocol in paths:
            paths[protocol].update(module_paths.get(protocol, {}))
        user_allowed += module_paths.get('user_allowed', [])
    
    paths['user_allowed'] = user_allowed
    return paths


