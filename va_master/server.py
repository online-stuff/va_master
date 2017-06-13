from .api.handler import ApiHandler, LogMessagingSocket
import tornado.ioloop
import tornado.web
import tornado.gen
import json
import os
from tornado import httpclient
#from bs4 import BeautifulSoup



class IndexHandler(tornado.web.RequestHandler):
    """Handles the index page of the dashboard."""

    def initialize(self, path):
        index_path = os.path.join(path, 'index.html')
        with open(index_path, 'r') as f:
            self.index_code = f.read()

    def get(self):
        self.write(self.index_code)
        self.flush()
        self.finish()

class ProxyHandler(tornado.web.RequestHandler):
    """Handles proxy for icinga."""
    def prepare(self):
        #print ("In proxy, ", str(self.request))
        url = "http://192.168.111.198/"  + self.request.uri.replace('/proxy/', '')
        #print ("URL", url)
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', 'Cookie': 'login_region="http://localhost:5000/v2.0"; grafana_sess=b6aa167ef19f9618; Icingaweb2=jm4bt120rh5k5jb0rirg1mpq45o83nc9; icingaweb2-tzo=3600-0'}

        try:
            http_client = httpclient.HTTPClient()
            headers.update(self.request.headers)
            #print ("HEADERS", headers)
            r = http_client.fetch(httpclient.HTTPRequest(url, self.request.method, headers))
            response = r.body
            if not any(x in url for x in ['js', 'css', 'font', 'svg', 'png', 'jpg', 'octet']):
                soup = BeautifulSoup(response, "lxml")
                for i in soup.findAll(href=True):
                    i['href'] = i['href'][1:]
                for i in soup.findAll(src=True):
                    i['src'] = i['src'][1:]
                response = str(soup)
        except httpclient.HTTPError as e:
            # HTTPError is raised for non-200 responses; the response
            # can be found in e.response.
            print("Error: " + str(e))
            print e.response
        except Exception as e:
            # Other errors are possible, such as IOError.
            print("Error: " + str(e))
        #print response
        #print r.headers
        http_client.close()
        self.set_header('Content-Type', r.headers['Content-Type'])
        self.set_status(200)
        self.write(response)
        #self.flush()
        self.finish()


class DebugStaticHandler(tornado.web.StaticFileHandler):
    """A static file handler that has debug features like no asset caching."""

    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')


def get_app(config):
    path_settings = {'path': config.server_static_path}

    app = tornado.web.Application([
        (r"/", IndexHandler, path_settings),
        (r"/api/(.*)", ApiHandler, {'config': config}),
        (r"/static/(.*)", DebugStaticHandler, path_settings), 
        (r"/log/(.*)", LogMessagingSocket),
        (r"/proxy/(.*)", ProxyHandler),

    ])
    # TODO: If config.release, disable debug mode for static assets
    # Note: running the debug mode is not dangerous in production, but it's slower.
    return app

