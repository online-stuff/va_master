import tornado.web, tornado.websocket
import tornado.gen

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from . import url_handler
from login import get_current_user, user_login
import json, datetime, syslog


#This will probably not be used anymore, keeping it here for reasons. 



class ApiHandler(tornado.web.RequestHandler):
    def initialize(self, config, include_version=False):
        self.config = config
        self.datastore = config.datastore
        self.data = {}
        try:
            self.paths = url_handler.gather_paths()
        except: 
            import traceback
            traceback.print_exc()
            return
        self.salt_client = None

    def json(self, obj, status=200):
#        print ('I am in json with ', obj)
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        self.write(json.dumps(obj))
        self.finish()


    def has_error(self, result):
        """ Returns True if result is a string which contains a salt error. May need more work, but is fine for now. """
        exceptions = [
            "The minion function caused an exception",
            "is not available",
        ]
        return any([i in result for i in exceptions])


    def formatted_result(self, result):
        """ Returns True if the result is formatted properly. The format for now is : {'data' : {'field' : []}, 'success' : :True/False, 'message' : 'Information. Usually empty if successful. '} """
        try: 
            result_fields = ['data', 'success', 'message']
            return set(result.keys()) == set(result_fields)
        except: 
            print ('Error with testing formatted result - probably is ok. ')
            return False


    @tornado.gen.coroutine
    def exec_method(self, method, path, data):
        self.data = data
        print ('My data is : ', data)
        self.data['method'] = method
        api_func = self.paths[method][path]
        if api_func != user_login: 
            try: 
                yield self.log_message(path, data)

                user = yield get_current_user(self)

                if not user: 
                    self.json({'success' : False, 'message' : 'User not authenticated properly. ', 'data' : {}})
                elif user['type'] == 'user' and path not in self.paths.get('user_allowed', []): 
                    self.json({'success' : False, 'message' : 'User does not have appropriate privileges. ', 'data' : {}})
            except: 
                import traceback
                traceback.print_exc()
        try: 
            result = yield api_func(self)
            if self.formatted_result(result): raise tornado.gen.Return(result)
            if self.has_error(result): 
                result = {'success' : False, 'message' : result, 'data' : {}} 
            else: 
                result = {'success' : True, 'message' : '', 'data' : result}
        except Exception as e: 
            result = {'success' : False, 'message' : 'There was an error performing a request : ' + e.message, 'data' : {}}
            import traceback
            traceback.print_exc()

        self.json(result)

    @tornado.gen.coroutine
    def get(self, path):
        args = self.request.query_arguments
        result = yield self.exec_method('get', path, {x : args[x][0] for x in args})


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
    def log_message(self, path, data):

        user = yield url_handler.login.get_current_user(self)
        message = json.dumps({
            'type' : 'POST', 
            'user' : user['username'], 
            'user_type' : user['type'], 
            'path' : path, 
            'data' : data, 
            'time' : str(datetime.datetime.now()),
        })
        print ('Logging message: ', message)
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
        self.socket.write_message(json.dumps(last_line))


class LogMessagingSocket(tornado.websocket.WebSocketHandler):

    #Socket gets messages when opened
    @tornado.web.asynchronous
    @tornado.gen.engine
    def open(self, no_messages = 5, logfile = '/var/log/vapourapps/va-master.log'):
        print ('Opened socket. ')
        self.logfile = logfile
        with open(logfile) as f: 
            self.messages = f.read().split('\n')
        self.messages = self.messages
        self.write_message(json.dumps(self.messages[-no_messages:]))

        log_handler = LogHandler(self)
        observer = Observer()
        observer.schedule(log_handler, path = '/var/log/vapourapps/')
        print ('Started log handler.')
        observer.start()
        
    def get_messages(message):
        return self.messages[-message['number_of_messages']:]

    def check_origin(self, origin): 
        return True

    @tornado.gen.coroutine
    def on_message(self, message): 
        print ('Something happened with the log!')
        try:
            message = json.loads(message)
            reply = {
                'get_messages' : self.get_messages
            }[message['action']]
        except: 
            import traceback
            traceback.print_exc()
        self.write_message(reply(message))

