import tornado.gen

def get_endpoints():
    return {
        'get': {
            'status': status
        }
    }

@tornado.gen.coroutine
def status(handler):
    handler.json({'e': True})
    raise tornado.gen.Return()
    handler.json({'a': 5})
