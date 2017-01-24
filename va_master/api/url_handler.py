from . import *
import sys
import types



def imports():
    for name, val in globals().items():
        if isinstance(val, types.ModuleType):
            yield val


def gather_paths():
    paths = {'get' : {}, 'post' : {}}

    api_modules = [x for x in imports()]
    print ('All modules are : ', api_modules)
    api_modules = [x for x in api_modules if getattr(x, 'get_paths', None)]
    print ('Api modules: ', api_modules)
    for api_module in api_modules:
        module_paths = api_module.get_paths()
        for protocol in paths:
            paths[protocol].update(module_paths.get(protocol, {}))
    return paths
