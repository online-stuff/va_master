import tornado.web
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from . import status, login, hosts, apps, panels
import json


paths = {
    'get' : {
        'status' : status.status, 

        'drivers' : hosts.list_drivers, 
        'hosts' : hosts.list_hosts, 
        'hosts/reset' : hosts.reset_hosts, 
        
        'states' : apps.get_states, 
        'states/reset' : apps.reset_states, 


        'panels' : panels.get_panels, 
        'panels/get_panel' : panels.get_panel_for_user, 
    },

    'post' : {
        'login' : login.user_login, 
        
        'hosts/new/validate_fields' : hosts.validate_newhost_fields, 
        'hosts/info' : hosts.get_host_info, 
        'hosts/delete' : hosts.delete_host, 

        'apps' : apps.launch_app, 
        'state/add' : apps.manage_states,

        'panel_action' : panels.panel_action, 
    }

}

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
    def exec_method(self, method, path, data):
        self.data = data
        try:
            yield paths[method][path](self)
        except: 
            import traceback
            traceback.print_exc()

    @tornado.gen.coroutine
    def get(self, path):
        yield self.exec_method('get', path, self.request.query_arguments)

    @tornado.gen.coroutine
    def post(self, path):
        yield self.exec_method('post', path, json.loads(self.request.body))

