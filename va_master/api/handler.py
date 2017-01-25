import tornado.web, tornado.websocket
import tornado.gen

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from . import status, login, hosts, apps, panels
import json, datetime, syslog

#This will probably not be used anymore, keeping it here for reasons. 
paths = {
    'get' : {
        'status' : status.status, 

        'drivers' : hosts.list_drivers, 
        'hosts' : hosts.list_hosts, 
        'hosts/reset' : hosts.reset_hosts, 
        
        'states' : apps.get_states, 
        'states/reset' : apps.reset_states, 

        'panels/reset_panels': panels.reset_panels, #JUST FOR TESTING
        'panels/new_panel' : panels.new_panel, #JUST FOR TESTING
        'panels' : panels.get_panels, 
        'panels/get_panel' : panels.get_panel_for_user, 
    },
    'post' : {
        'login' : login.user_login, 
        
        'hosts/new/validate_fields' : hosts.validate_newhost_fields, 
        'hosts/info' : hosts.get_host_info, 
        'hosts/delete' : hosts.delete_host, 

        'state/add' : apps.create_new_state,

        'panel_action' : panels.panel_action, 
        'panels/action' : panels.panel_action #must have instance_name and action in data, ex: panels/action instance_name=nino_dir action=list_users
    }
}

paths = {'get' : {}, 'post' : {}}

for api_module in [apps, login, hosts, apps, panels]: 
    module_paths = api_module.get_paths()
    for protocol in paths: 
        paths[protocol].update(module_paths.get(protocol, {}))

print (paths)

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

            message = 'User ' +  user['username'] + ' of type ' +  user['type'] + ' performed a POST request on ' +  path + ' with data ' + str(data) + ' at time ' + str(datetime.datetime.now())
            print ('Logging: ', message)
            syslog.syslog(syslog.LOG_INFO | syslog.LOG_LOCAL0, message)
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



class LogHandler(FileSystemEventHandler):
    def __init__(self, socket):
        self.socket = socket
        super(LogHandler, self).__init__()

    def on_modified(self, event):
        log_file = event.src_path
        with open(log_file) as f: 
            log_file = [x for x in f.read().split('\n') if x]
        last_line = log_file[-1]
        self.socket.write_message(last_line)


class LogMessagingSocket(tornado.websocket.WebSocketHandler):

    #Socket gets messages when opened
    @tornado.web.asynchronous
    @tornado.gen.engine
    def open(self, no_messages = 5, logfile = '/var/log/vapourapps/va-master.log'):
        print ('I am open')
        self.logfile = logfile
        with open(logfile) as f: 
            self.messages = f.read().split('\n')
        self.messages = self.messages
        self.write_message(json.dumps(self.messages[-no_messages:]))

        log_handler = LogHandler(self)
        observer = Observer()
        observer.schedule(log_handler, path = '/var/log/vapourapps/')
        observer.start()
        
    def get_messages(message):
        return self.messages[-message['number_of_messages']:]

    def check_origin(self, origin): 
        return True

    @tornado.gen.coroutine
    def on_message(self, message): 
        message = json.loads(message)
        reply = {
            'get_messages' : self.get_messages
        }[message['action']]
        self.write_message(reply(message))

