from tornado.gen import coroutine, Return

def initialize(handler):
    handler.add_get_endpoint('status', status)

@coroutine
def status(handler):
    handler.json({'status': 'It works!'})