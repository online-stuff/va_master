import tornado.httpserver
import tornado.ioloop
import cli
import sys
import ssl
from . import config, api_server

def bootstrap():
    """Starts the master with all its components, and provides the configuration
    data to all the components."""

    my_config = config.Config()
    my_config.init_handler({})
    my_config.logger.info('Starting deploy handler...')

    app = api_server.get_app(my_config)
    #ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    #ssl_ctx.load_cert_chain("/root/keys/fortornado/evo-master.crt", "/root/keys/fortornado/evo-master.key")

    http_server = tornado.httpserver.HTTPServer(app, )#ssl_options=ssl_ctx)
    http_server.listen(443)
    tornado.ioloop.IOLoop.current().start()
#    tornado.ioloop.IOLoop.instance().start()
#    app.listen(my_config.server_port)
