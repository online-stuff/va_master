import tornado.web, tornado.websocket
import tornado.gen

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor   # `pip install futures` for python2

from login import get_current_user, user_login
import json, datetime, syslog
import pkgutil
import traceback
import sys
import os
import importlib
from ..config import logger

def invalid_url(handler):
    raise Exception('Invalid URL : ' + handler.data['path'] +' with method : ' + handler.data['method'])

# Don't import these modules as endpoints
ENDPOINT_BLACKLIST = ('apps', 'triggers')

def get_endpoints():
    '''Gets the endpoints of the modules in this package in the form
    {'module_name': {'get': ..., 'post': ...}, ...}
    '''

    # Get all modules in the current package (.api)
    this_dir = os.path.dirname(__file__)
    mods = pkgutil.iter_modules([this_dir])
    endpoints = {'get': {}, 'post': {}}
    for _, module_name, _ in mods:
        if module_name in ENDPOINT_BLACKLIST: continue

        try:
            mod_endpoints = importlib.import_module('.{}'.format(module_name), __package__) \
                .get_endpoints()
            if 'get' in mod_endpoints:
                endpoints['get'].update(mod_endpoints['get'])
            if 'post' in mod_endpoints:
                endpoints['post'].update(mod_endpoints['post'])
        except AttributeError:
            logger.debug('Cannot import {} as endpoint (it doesn\'t have '
            'get_endpoints()).'.format(module_name))
    return endpoints

# Only query endpoints once (it's an expensive operation)
# These can't change at runtime.
all_endpoints = get_endpoints()

class ApiHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers= 4)

    def initialize(self, config, include_version=False):
        self.config = config
        self.datastore = config.datastore
        self.data = {}
        self.endpoints = all_endpoints
        print(self.endpoints)
        self.salt_client = None

    def json(self, obj, status=200):
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        self.write(json.dumps(obj))
        self.finish()

    @tornado.gen.coroutine
    def exec_method(self, method, path, data):
        self.data = data
        self.data['method'] = method
        api_func = self.endpoints[method].get(path)
        print ('Getting a call at ', path, ' with data ', data, ' and will call function: ', api_func)
        res = yield api_func(self)
        self.json(res)

    @tornado.gen.coroutine
    def get(self, path):
        args = self.request.query_arguments
        t_args = args
        for x in t_args:
            if len(t_args[x]) == 1:
                args[x] = args[x][0]
        try:
#            result = yield self.exec_method('get', path, {x : args[x][0] for x in args})
            result = yield self.exec_method('get', path, args)

        except:
            import traceback
            traceback.print_exc()

    @tornado.gen.coroutine
    def delete(self, path):
        try:
            data = json.loads(self.request.body)
            result = yield self.exec_method('delete', path, data)
        except:
            import traceback
            traceback.print_exc()

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

            yield self.exec_method('post', path, data)
        except:
            import traceback
            traceback.print_exc()


    @tornado.gen.coroutine
    def log_message(self, path, data, func):

        user = yield url_handler.login.get_current_user(self)
        message = json.dumps({
            'type' : data['method'],
            'function' : func.func_name,
            'user' : user['username'],
            'user_type' : user['type'],
            'path' : path,
            'data' : data,
            'time' : str(datetime.datetime.now()),
        })
        try:
            syslog.syslog(syslog.LOG_INFO | syslog.LOG_LOCAL0, message)
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
        try:
            self.socket.write_message(json.dumps(last_line))
        except: 
            pass


class LogMessagingSocket(tornado.websocket.WebSocketHandler):

    #Socket gets messages when opened
    @tornado.web.asynchronous
    @tornado.gen.engine
    def open(self, no_messages = 100, logfile = '/var/log/vapourapps/va-master.log'):
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
        try:
            message = json.loads(message)
            reply = {
                'get_messages' : self.get_messages
            }[message['action']]
        except: 
            import traceback
#            traceback.print_exc()
        self.write_message(reply(message))

