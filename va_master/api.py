import tornado.web
import tornado.gen
import json
import base64
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from concurrent.futures import ThreadPoolExecutor
import salt
import salt.cloud

@tornado.gen.coroutine
def handle_login(handler):
    body = None

    try:
        body = json.loads(handler.request.body)
    except:
        handler.json({'error': 'bad_body'}, 400)

    if 'username' not in body or 'password' not in body:
        handler.json({'error': 'bad_body'}, 400)
    username = body['username']
    password = body['password']
    if username == 'admin' and password=='admin':
        handler.json({'token': 'aUxL4nlpPtyq'})
    else:
        handler.json({'error': 'wrong_auth'}, 401)

@tornado.gen.coroutine
def handle_add_host(handler):
    try:
        body = json.loads(handler.request.body)
        name = body['name']
        driver = body['driver']
    except:
        handler.json({'error': 'bad_body'})
    client = AsyncHTTPClient()
    resp = yield client.fetch('http://127.0.0.1:8500/v1/kv/hosts')
    resp = json.loads(resp.body)[0]['Value']
    resp = json.loads(base64.b64decode(resp))
    resp+= [{'name': name, 'is_deletable': True, 'driver': driver}]
    req = HTTPRequest('http://127.0.0.1:8500/v1/kv/hosts', method='PUT',
        body=json.dumps(resp))
    yield client.fetch(req)
    handler.json({'cool': True})

@tornado.gen.coroutine
def handle_get_hosts(handler):
    host_list = []
    client = AsyncHTTPClient()
    error = False
    try:
        resp = yield client.fetch('http://127.0.0.1:8500/v1/kv/hosts')
        resp = json.loads(resp.body)[0]['Value']
        resp = json.loads(base64.b64decode(resp))
        handler.json({'hosts': resp})
    except ZeroDivisionError:
        req = HTTPRequest('http://127.0.0.1:8500/v1/kv/hosts', method='PUT',
            body='[]')
        yield client.fetch(req)
        handler.json({'error': 'consul_404'}, 400)
        error = True

executor = ThreadPoolExecutor(max_workers=4)

def new_instance(name):
    cl = salt.cloud.CloudClient('/etc/salt/cloud')
    res = cl.create(provider='vapps', names=[name], image='VAinstance',
  size='va-small', securitygroup='default', grains={'roles': 'samba'} )

@tornado.gen.coroutine
def handle_launch_app(handler):
    try:
        name = json.loads(handler.request.body)['name']
    except:
        handler.json({'error': 'bad_body'}, 400)

    yield executor.submit(new_instance, name)
    handler.json({'cool': True})

class ApiHandler(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config

    def json(self, obj, status=200):
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        self.write(json.dumps(obj))
        self.finish()

    @tornado.gen.coroutine
    def get(self, path):
        if path == 'version':
            self.json({'master_version': self.config.pretty_version()})
        elif path == 'hosts':
            yield handle_get_hosts(self)
        else:
            self.json({'error': 'not_found'}, 404)

    @tornado.gen.coroutine
    def post(self, path):
        if path == 'login':
            yield handle_login(self)
        elif path == 'hosts':
            yield handle_add_host(self)
        elif path == 'apps':
            yield handle_launch_app(self)
        else:
            self.json({'error': 'not_found'}, 404)
