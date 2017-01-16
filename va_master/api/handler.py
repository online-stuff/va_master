import tornado.web
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from . import status, login, hosts, apps, panels
import json, datetime


paths = {
    'get' : {
        'apps/vpn_users' : apps.get_openvpn_users,
        'apps/add_app' : apps.add_app,
        'apps/get_actions' : apps.get_user_actions, 

        'status' : status.status, 

        'drivers' : hosts.list_drivers, 
        'hosts' : hosts.list_hosts, 
        'hosts/reset' : hosts.reset_hosts, 
        
        'states' : apps.get_states, 
        'states/reset' : apps.reset_states, 

        'panels/new_panel' : panels.new_panel,
        'panels' : panels.get_panels, 
        'panels/get_panel' : panels.get_panel_for_user, 
    },
    'post' : {
        'login' : login.user_login, 
        
        'hosts/new/validate_fields' : hosts.validate_newhost_fields, 
        'hosts/info' : hosts.get_host_info, 
        'hosts/delete' : hosts.delete_host, 

        'apps' : apps.launch_app, 
        'apps/action' : apps.perform_instance_action, 
        'apps/add_vpn_user': apps.add_openvpn_user,
        'apps/revoke_vpn_user': apps.revoke_openvpn_user,
        'apps/list_user_logins': apps.list_user_logins,
        'apps/download_vpn_cert': apps.download_vpn_cert,


        'state/add' : apps.create_new_state,

        'panel_action' : panels.panel_action, 
        'panels/action' : panels.panel_action #must have instance_name and action in data, ex: panels/action instance_name=nino_dir action=list_users

    }

}

class ApiHandler(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config
        self.datastore = config.datastore
        self.data = {}

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
        args = self.request.query_arguments
        yield self.exec_method('get', path, {x : args[x][0] for x in args})

    @tornado.gen.coroutine
    def post(self, path):
        try: 
            try: 
                if 'json' in self.request.headers['Content-Type']: 
                    data = json.loads(self.request.body)
                else:
                    data = {self.request.arguments[x][0] for x in self.request.arguments}
                    data.update(self.request.files)
            except ValueError: 
                import traceback
                traceback.print_exc()
                data = {}
            user = yield login.get_current_user(self)
            yield self.exec_method('post', path, data)
            yield self.config.deploy_handler.store_action(user, path, data)

        except: 
            import traceback
            traceback.print_exc()


    @tornado.gen.coroutine
    def serve_file(self, file_path, chunk_size = 4096):
        try: 
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Disposition', 'attachment; filename=' + file_path)
            with open(file_path, 'r') as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    self.write(data)
            self.finish()
        except: 
            import traceback
            traceback.print_exc()


