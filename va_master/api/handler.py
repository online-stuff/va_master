import tornado.web
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from . import status, login, hosts, apps, panels
import json

class ApiHandler(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config
        self.datastore = config.datastore
        self.data = {}
        self.deploy_handler = None

    def json(self, obj, status=200):
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        self.write(json.dumps(obj))
        self.finish()

    @tornado.gen.coroutine
    def get(self, path):
        self.data = self.request.query_arguments
        try:
            if path == 'status':
                yield status.status(self)
            elif path == 'drivers':
                yield hosts.list_drivers(self)
            elif path == 'hosts':
                yield hosts.list_hosts(self)
            elif path == 'states': 
                yield apps.get_states(self)
            elif path == 'panel_action': 
                yield panels.panel_action(self)
            else:
                self.json({'error': 'not_found'}, 404)
        except: 
            import traceback
            traceback.print_exc()

    @tornado.gen.coroutine
    def post(self, path):
        try:
            print ('Body is : ', self.request.body)
            self.data = json.loads(self.request.body)

            print (self.data, ' is data')
            if path == 'login':
                yield login.user_login(self)

            elif path == 'hosts/new/validate_fields':
                yield hosts.validate_newhost_fields(self)
            elif path == 'hosts/info':
                yield hosts.get_host_info(self)

            elif path == 'apps':
                yield apps.launch_app(self)
            elif path == 'state/add': 
                yield apps.manage_states(self)
            else:
                self.json({'error': 'not_found'}, 404)
        except: 
            import traceback
            traceback.print_exc()
