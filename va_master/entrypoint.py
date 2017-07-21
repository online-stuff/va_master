import tornado.httpserver
import tornado.ioloop
import sys
import ssl
from . import config, httpserver

def bootstrap(master_config=None):
    """Starts the master with all its components, and provides the configuration
    data to all the components."""

    if master_config is None:
        master_config = config.Config()
    
    app = httpserver.get_app(master_config)
    #ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    #ssl_ctx.load_cert_chain("/root/keys/fortornado/evo-master.crt", "/root/keys/fortornado/evo-master.key")

    from . import consul
    consul.ConsulProcess(master_config).start()

    my_serv = tornado.httpserver.HTTPServer(app, )#ssl_options=ssl_ctx)
    my_serv.listen(443)
    tornado.ioloop.IOLoop.current().start()
#    tornado.ioloop.IOLoop.instance().start()
#    app.listen(my_config.server_port)
