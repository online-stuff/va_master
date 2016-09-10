import tornado.gen

@tornado.gen.coroutine
def status(handler):
    init = True
    try:
        yield handler.datastore.get('initialized')
    except handler.datastore.NotFound:
        init = False
    handler.json({'is_initialized': init})
