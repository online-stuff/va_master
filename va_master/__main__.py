import tornado.httpserver
import tornado.ioloop
import tornado.options
import cli
import sys
import ssl

def bootstrap():
    """Starts the master with all its components, and provides the configuration
    data to all the components."""

    from . import config, server

    tornado.options.parse_command_line()

    my_config = config.Config()
    my_config.init_handler({})
    my_config.logger.info('Starting deploy handler...')

    app = server.get_app(my_config)
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
#    ssl_ctx.load_cert_chain("/root/keys/fortornado/cert.crt", "/root/keys/fortornado/server.key")
    ssl_ctx.load_cert_chain("/opt/va_master/ssl/cert.crt", "/opt/va_master/ssl/server.key")

    http_server = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx)
    http_server.listen(443)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    if 'start' in sys.argv: 
        bootstrap()
    else: 
        cli.entry()
