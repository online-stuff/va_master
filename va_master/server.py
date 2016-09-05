import tornado.ioloop
import tornado.web
import tornado.gen
import json
from . import api

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""<!DOCTYPE html>
            <head>
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css">
                <link rel="stylesheet" href="/static/style.css">
                <script type="text/javascript" src="https://code.jquery.com/jquery-2.2.4.min.js"></script>
                <script type="text/javascript" src="/static/bundle.js"></script>
            </head>
            <body class="nav-md"> <div id="body-wrapper"></body> </body>
            </html>""")

class DebugStaticHandler(tornado.web.StaticFileHandler):
    """A static file handler that has debug features like no asset caching."""

    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')


def start(config):
    app = tornado.web.Application([
        (r"/", MainHandler),
        (r"/api/(.*)", api.ApiHandler, {'config': config}),
        (r"/static/(.*)", DebugStaticHandler, {'path':config.server_static_path})
    ])
    # TODO: If config.release, disable debug mode for static assets
    # Note: running the debug mode is not dangerous in production, but it's slower.
    app.listen(config.server_port)
    tornado.ioloop.IOLoop.current().start()
