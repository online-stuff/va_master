import tornado.web
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from . import login

class ApiHandler(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config
        self.datastore = config.datastore

    def json(self, obj, status=200):
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        self.write(json.dumps(obj))
        self.finish()

    @tornado.gen.coroutine
    def get(self, path):
        if path == 'drivers':
            yield hosts.list_drivers(self)
        elif path == 'hosts':
            yield hosts.list_hosts(self)
        else:
            self.json({'error': 'not_found'}, 404)

    @tornado.gen.coroutine
    def post(self, path):
        if path == 'login/admin':
            yield login.admin_login(self)
        elif path == 'login/ldap':
            yield login.ldap_login(self)
        elif path == 'hosts':
            yield hosts.new_host(self)
        elif path == 'apps':
            yield apps.launch_app(self)
        else:
            self.json({'error': 'not_found'}, 404)
