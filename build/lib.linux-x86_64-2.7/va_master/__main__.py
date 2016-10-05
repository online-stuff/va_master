def bootstrap():
    """Starts the master with all its components, and provides the configuration
    data to all the components."""

    from . import config, server

    my_config = config.Config()
    my_config.logger.info('Starting deploy handler...')

    app = server.get_app(my_config)
    app.listen(my_config.server_port)

    def say_hello():
        print("Hello, it's me.")
    from tornado.ioloop import PeriodicCallback, IOLoop
    ioloop = IOLoop.instance()

    cb = PeriodicCallback(say_hello, 1000, ioloop)
    cb.start()

    ioloop.start()

if __name__ == '__main__':
    bootstrap()
