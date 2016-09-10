def bootstrap():
    """Starts the master with all its components, and provides the configuration
    data to all the components."""

    from . import config, server

    my_config = config.Config()
    logger = my_config.logger
    logger.info('Starting deploy handler...')
    server.start(my_config)

if __name__ == '__main__':
    bootstrap()
