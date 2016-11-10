import tornado.gen

@tornado.gen.coroutine
def status(handler):
    handler.json({'e': True})
    raise tornado.gen.Return()
    handler.json({'a': 5})
