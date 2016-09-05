from . import server

def bootstrap(config):
    """Starts the master with all its components, and provides the configuration
    data to all the components."""
    
    logger = config.logger
    logger.info('Starting deploy handler...')
    server.start(config)
