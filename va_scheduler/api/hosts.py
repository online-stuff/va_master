from .login import auth_only

@auth_only
def list_hosts(handler):
    handler.json({'hi': True})

def list_drivers(handler):
    pass

def new_host(handler):
    pass
