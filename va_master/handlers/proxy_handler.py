import tornado.web, tornado.websocket
import tornado.gen

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.concurrent import run_on_executor, Future

import json, datetime, syslog, pytz

class ProxyHandler(tornado.web.RequestHandler):
    status = 200

    @tornado.gen.coroutine
    def initialize(self, config):
        try:
            self.datastore_handler = config.datastore_handler
        except: 
            import traceback
            traceback.print_exc()

    @tornado.gen.coroutine
    def fetch_server_data(self, proxy_url, data = {}, method = 'GET'):
        result = None
        try:
            resp = yield AsyncHTTPClient().fetch(proxy_url, headers=self.request.headers, body = json.dumps(data), method = method)
            self.set_status(resp.code)
            for k,v in resp.headers.get_all():
                self.add_header(k, v)

            result = resp
        except: 
            import traceback
            traceback.print_exc()

        raise tornado.gen.Return(result)


    @tornado.gen.coroutine
    def get_url_from_path(self, path, auth = {}):
        path = path.split('/')
        server_name, proxy_path = path[0], '/'.join(path[1:])

        server = yield self.datastore_handler.get_object('server', server_name = server_name)
        server_path = server.get('proxy_path') or server.get('ip_address')

        if not server_path: 
            raise tornado.gen.Return('Server ' + server['server_name'] + ' has no proxy_path or ip_address, so I cannot go to its proxy path. ')

        if auth: 
            full_path = 'http://%s:%s@%s/%s' % (auth['username'], auth['password'], server_path, proxy_path)
        else: 
            full_path = 'http://%s/%s' % (server_path, proxy_path)

        raise tornado.gen.Return(full_path)


    @tornado.gen.coroutine
    def get(self, path):
        data = self.request.query_arguments
        for x in data:
            if len(data[x]) == 1:
                data[x] = data[x][0]

        path = yield self.get_url_from_path(path)
        data = yield self.fetch_server_data(path, data)

        self.write(data)


    @tornado.gen.coroutine
    def post(self, path):
        auth = {}

        try: 
            if 'json' in self.request.headers['Content-Type']: 
                try:
                    data = json.loads(self.request.body)
                except: 
                    raise Exception('Bad json in request body : ', self.request.body)
            else:
                data = {self.request.arguments[x][0] for x in self.request.arguments}
                data.update(self.request.files)

            if 'username' and 'password' in data: 
                auth = data

            path = yield self.get_url_from_path(path, auth = auth)

            result = yield self.fetch_server_data(path, data, method = 'POST')
            self.write(result.body)

            self.set_status(result.code)

            for k, v in result.headers.get_all():
                self.set_header(k, v)
            self.set_header('Content-Length', str(len(result.body)))
            self.flush()
        except:
            import traceback
            traceback.print_exc()


