import tornado.web
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from . import status, login, hosts, apps
import json

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
        if path == 'status':
            yield status.status(self)
        elif path == 'drivers':
            yield hosts.list_drivers(self)
        elif path == 'hosts':
            yield hosts.list_hosts(self)
        else:
            self.json({'error': 'not_found'}, 404)

    @tornado.gen.coroutine
    def post(self, path):
        if path == 'login':
            yield login.admin_login(self)
        elif path == 'hosts/new/validate_fields':
            yield hosts.validate_newhost_fields(self)
        elif path == 'apps':
            yield apps.launch_app(self)
        else:
            self.json({'error': 'not_found'}, 404)
