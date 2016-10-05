def bootstrap():
    """Starts the master with all its components, and provides the configuration
    data to all the components."""

    from . import config, server

    my_config = config.Config()
    my_config.logger.info('Starting deploy handler...')

    app = server.get_app(my_config)
    app.listen(my_config.server_port)
    from tornado.ioloop import PeriodicCallback, IOLoop
    ioloop = IOLoop.instance()

    ioloop.start()

if __name__ == '__main__':
    bootstrap()
