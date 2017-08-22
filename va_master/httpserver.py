from .api import ApiHandler, LogMessagingSocket
import tornado.ioloop
import tornado.web
import tornado.gen
import json
import os
from tornado import httpclient


class IndexHandler(tornado.web.RequestHandler):
    '''Handles the index page of the dashboard.'''

    def initialize(self, path):
        index_path = os.path.join(path, 'index.html')
        with open(index_path, 'r') as f:
            self.index_code = f.read()

    def get(self):
        self.write(self.index_code)
        self.flush()
        self.finish()

DISABLE_CACHE = True # TODO: Make it possible to cache in production?

class StaticHandler(tornado.web.StaticFileHandler):
    '''A static file handler for front-end assets.'''

    def set_extra_headers(self, path):
        if DISABLE_CACHE:
            self.set_header('Cache-Control', 'no-store, no-cache, ' \
                'must-revalidate, max-age=0')


def get_app(config):
    path_settings = {'path': config.server_static_path}

    app = tornado.web.Application([
        (r"/", IndexHandler, path_settings),
        (r"/api/(.*)", ApiHandler, {'config': config}),
        (r"/static/(.*)", StaticHandler, path_settings),
        (r"/log/(.*)", LogMessagingSocket),
    ])
    # TODO: If config.release, disable debug mode for static assets
    # Note: running the debug mode is not dangerous in production, but it's slower.
    return app

