import tornado.web, tornado.websocket
import tornado.gen

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.concurrent import run_on_executor, Future

import json, datetime, syslog, pytz

class ProxyHandler():
    status = 200


    def __init__(self, config):
        self.datastore_handler = config.datastore_handler

    @tornado.gen.coroutine
    def fetch_server_data(self, proxy_url, data = '', method = 'GET', headers = {}):
        result = None
        try:
            kwargs = {'method' : method}
            kwargs['headers'] = headers or self.request.headers
            if 'Content-Length' in kwargs['headers']: 
                kwargs['headers'].pop('Content-Length')
            if 'Content-Type' in kwargs['headers']: 
                data = json.dumps(data)
            if not method == 'GET': 
                kwargs['body'] = data
            print ('Headers are : ', kwargs['headers'].keys())
            print ('Using url : ', proxy_url, ' with kwargs', kwargs)

            fetch_request = HTTPRequest(proxy_url, **kwargs)
            if fetch_request.body:
                fetch_request.headers['Content-Length'] = str(len(fetch_request.body))
            print ('Fetch request is : ', fetch_request.body)
            result = yield AsyncHTTPClient().fetch(fetch_request)
            print ('Have result: ', result.body)
        except: 
            import traceback
            traceback.print_exc()

        raise tornado.gen.Return(result)

    def get_server_path(self, server, auth):
        server_path =  server.get('ip_address')

        if not server_path: 
            raise tornado.gen.Return('Server ' + server + ' has no proxy_path or ip_address. ')

        auth_path = ''
        if auth: 
            auth_path = auth['username'] + ':' + auth['password'] + '@'
        server_path = 'http://{auth_path}{server_path}'.format(auth_path = auth_path, server_path = server_path)
        return server_path
          
    @tornado.gen.coroutine
    def get_url_from_path(self, server_name, proxy_path, auth = {}):
        print ('Proxy path is : ', proxy_path, ' server name is : ', server_name)
        server = yield self.datastore_handler.get_object('server', server_name = server_name)

        server_path = server.get('proxy_path')
        if not server_path: 
            if not server: 
                server = {'ip_address' : server_name}
            server_path = self.get_server_path(server, auth)


        full_path = '/'.join([server_path, proxy_path])
        print ('Full path is : ', full_path)
        raise tornado.gen.Return(full_path)

    @tornado.gen.coroutine
    def handle_request(self, api_handler, server, method, path, data):

        method = method.upper()
        path = yield self.get_url_from_path(server, path)
        result = yield self.fetch_server_data(path, data, method = method, headers = api_handler.request.headers)

        api_handler.set_header('Content-Length', str(len(result.body)))
        print ('Content length is : ', api_handler._headers['Content-Length'], ' and len is : ', len(result.body))
        print ('Writing to handler: ', result.body)
        api_handler.write(result.body)
#        for k, v in result.headers.get_all():
#            api_handler.set_header(k, v)
        api_handler.flush()


    @tornado.gen.coroutine
    def get(self, server, path):
        try:
            data = self.request.query_arguments
            for x in data:
                if len(data[x]) == 1:
                    data[x] = data[x][0]
    
            path = yield self.get_url_from_path(server, path)
            result = yield self.fetch_server_data(path, data)

            self.write(result.body)
            self.flush()
        except: 
            import traceback
            traceback.print_exc()


    @tornado.gen.coroutine
    def post(self, server, path):
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

            if 'username' in data and 'password' in data and data.get('use_auth'): 
                auth = data

            path = yield self.get_url_from_path(server, path)#, auth = auth)
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


