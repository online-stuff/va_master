import tornado.web, tornado.websocket
import tornado.gen

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.concurrent import run_on_executor, Future
from concurrent.futures import ThreadPoolExecutor   # `pip install futures` for python2

from . import url_handler
from login import get_current_user, user_login
import json, datetime, syslog, pytz
import dateutil.relativedelta
import dateutil.parser

from salt.client import LocalClient


def invalid_url(deploy_handler, path, method):
    raise Exception('Invalid URL : ' + path +' with method : ' + method)

class ApiHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers= 4)

    def initialize(self, config, include_version=False):
        self.config = config
        self.datastore = config.datastore
        self.data = {}
        self.paths = url_handler.gather_paths()
        self.salt_client = None

    #Temporary for testing
    #TODO remove in prod
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Authorization, Content-Type")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, DELETE, OPTIONS')


    def json(self, obj, status=200):
        if not obj: 
            return
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        self.write(json.dumps(obj))
        self.flush()
#        self.finish()


    def has_error(self, result):
        """ Returns True if result is a string which contains a salt error. May need more work, but is fine for now. """
        exceptions = [
            "The minion function caused an exception",
            "is not available",
            "Passed invalid arguments to",
            "ERROR",
        ]
        if type(result) == str: 
            has_error =  any([i in result for i in exceptions])
            if has_error: 
                print ('Salt error: ', result)
            return has_error
        else: return False


    def formatted_result(self, result):
        """ Returns True if the result is formatted properly. The format for now is : {'data' : {'field' : []}, 'success' : :True/False, 'message' : 'Information. Usually empty if successful. '} """
        try: 
            result_fields = ['data', 'success', 'message']
            result = (set (result.keys()) == set(result_fields))
            return result
        except: 
#            print ('Error with testing formatted result - probably is ok. ')
            return False


    def fetch_func(self, method, path, data):
        api_func = self.paths[method].get(path)

        print ('Getting a call at ', path, ' with data ', data, ' and will call function: ', api_func)

        if not api_func: 
            api_func = {'function' : invalid_url, 'args' : ['path', 'method']}

        return api_func

    @tornado.gen.coroutine
    def handle_user_auth(self, path):
        auth_successful = True
        try: 
            user = yield get_current_user(self)
            print ('User is : ', user)
            if not user: 
                self.json({'success' : False, 'message' : 'User not authenticated properly. ', 'data' : {}})
                auth_successful = False
            elif user['type'] == 'user' and path not in self.paths.get('user_allowed', []): 
                self.json({'success' : False, 'message' : 'User does not have appropriate privileges. ', 'data' : {}})
                auth_successful = False
        except Exception as e: 
            import traceback
            traceback.print_exc()

            self.json({'success' : False, 'message' : 'There was an error retrieving user data. ' + e.message, 'data' : {}})
            auth_successful = False

        user_functions = yield self.config.deploy_handler.get_user_functions(user.get('username'))
        if user_functions and path not in user_functions: 
            self.json({'success' : False, 'message' : 'User ' + user['username'] + ' tried to access ' + path + ' but it is not in their allowed functions : ' + str(user_functions)})
            auth_successful = False
   
        raise tornado.gen.Return(auth_successful)   

    @tornado.gen.coroutine
    def handle_func(self, api_func, data):
        try:
            api_func, api_kwargs = api_func.get('function'), api_func.get('args')       
            api_kwargs = {x : data.get(x) for x in api_kwargs if data.get(x)} or {}

            result = yield api_func(self.config.deploy_handler, **api_kwargs)

            if type(result) == dict: 
                if result.get('data_type', 'json') == 'file' : 
                    raise tornado.gen.Return(None)
            if self.formatted_result(result) or self.data.get('plain_result'): 
                pass 
            elif self.has_error(result): 
                result = {'success' : False, 'message' : result, 'data' : {}} 
            else: 
                result = {'success' : True, 'message' : '', 'data' : result}
        except tornado.gen.Return: 
            raise
        except Exception as e: 
            import traceback
            traceback.print_exc()

            result = {'success' : False, 'message' : 'There was an error performing a request : ' + str(e.message), 'data' : {}}
        raise tornado.gen.Return(result)
        



    @tornado.gen.coroutine
    def exec_method(self, method, path, data):
        self.data = data
        print ('In exec method, data is : ', data)
        self.data['method'] = method
        self.data['handler'] = self
        self.data['path'] = path

        user = yield get_current_user(self)
        data['dash_user'] = user

        api_func = self.fetch_func(method, path, data)

        if api_func['function'] not in [user_login]:#, url_serve_file_test]: 
            auth_successful = yield self.handle_user_auth(path)
            if not auth_successful: 
                raise tornado.gen.Return()

        result = yield self.handle_func(api_func, data)

        yield self.log_message(path = path, data = data, func = api_func['function'], result = result)

        self.json(result)

    @tornado.gen.coroutine
    def get(self, path):
        args = self.request.query_arguments
        t_args = args
        for x in t_args: 
            if len(t_args[x]) == 1: 
                args[x] = args[x][0]
        try:
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
                    try:
                        data = json.loads(self.request.body)
                    except: 
                        raise Exception('Bad json in request body : ', self.request.body)
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
    def options(self, path):
        self.set_status(204)
        self.finish()



    @tornado.gen.coroutine
    def log_message(self, path, data, func, result):

        data = {x : str(data[x]) for x in data}
        user = yield url_handler.login.get_current_user(self)
        if not user: 
            user = {'username' : 'unknown', 'type' : 'unknown'}
        message = json.dumps({
            'type' : data['method'], 
            'function' : func.func_name,
            'user' : user.get('username', 'unknown'), 
            'user_type' : user['type'], 
            'path' : path, 
            'data' : data, 
            'time' : str(datetime.datetime.now()),
            'result' : result,
        })
        try:
            syslog.syslog(syslog.LOG_INFO | syslog.LOG_LOCAL0, message)
        except: 
            import traceback
            traceback.print_exc()


    @tornado.gen.coroutine
    def send_data(self, source, kwargs, chunk_size):
        args = []
    
        #kwargs has a 'source_args' field for placement arguments sent to the source. For instance, for file.read(), we have to send the "size" argument as a placement argument. 
        if kwargs.get('source_args'): 
            args = kwargs.pop('source_args')

        offset = 0
        while True:
            print ('Calling ', source, ' with ', kwargs)
            data = source(*args, **kwargs)

            offset += chunk_size
            if 'kwarg' in kwargs: 
                if 'range_from' in kwargs['kwarg'].keys(): 
                    kwargs['kwarg']['range_from'] = offset            

            if type(data) == dict: #If using salt, it typically is formatted as {"minion" : "data"}
                if kwargs.get('tgt') in data: 
                    data = data[kwargs.get('tgt')]
            if not data:
                break

            if type(data) == str:
                self.write(data)
                self.flush()

            elif type(data) == Future: 
                self.flush()
                data = yield data
                raise tornado.gen.Return(data)

      


    @tornado.gen.coroutine
    def serve_file(self, source, chunk_size = 10**6, salt_source = {}, url_source = ''):

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=test.zip')

        try: 
            offset = 0

            if salt_source: 
                client = LocalClient()
                source = client.cmd
                kwargs = salt_source
                kwargs['kwarg'] = kwargs.get('kwarg', {})
                kwargs['kwarg']['range_from'] = 0
            elif url_source: 
                def streaming_callback(chunk):
                    self.write(chunk)
                    self.flush()
                source = AsyncHTTPClient().fetch
                request = HTTPRequest(url = url_source, streaming_callback = streaming_callback)
                request = url_source
                kwargs = {"request" : request, 'streaming_callback' : streaming_callback}
            else:
                f = open(source, 'r')
                source = f.read
                kwargs = {"source_args" : [chunk_size]}

            result = yield self.send_data(source, kwargs, chunk_size)
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
        try:
            last_line = log_file[-1]
            last_line = json.loads(last_line)

            msg = {"type" : "update", "message" : last_line}
#            self.socket.write_message(json.dumps(msg))
        except: 
            import traceback
            traceback.print_exc()


class LogMessagingSocket(tornado.websocket.WebSocketHandler):

    #Socket gets messages when opened
    @tornado.web.asynchronous
    @tornado.gen.engine
    def open(self, no_messages = 0, log_path = '/var/log/vapourapps/', log_file = 'va-master.log'):
        print ('Trying to open socket. ')
        try: 
            self.logfile = log_path + log_file
            try:
                with open(self.logfile) as f: 
                    self.messages = f.read().split('\n')
            except: 
                self.messages = []
            json_msgs = []
            for message in self.messages: 
                try:
                    j_msg = json.loads(message)
                except: 
                    continue
                json_msgs.append(j_msg)
            self.messages = json_msgs 
            yesterday = datetime.datetime.now() + dateutil.relativedelta.relativedelta(days = -1)

            init_messages = self.get_messages(yesterday, datetime.datetime.now())

            msg = {"type" : "init", "logs" : init_messages}
            self.write_message(json.dumps(msg))

            log_handler = LogHandler(self)
            observer = Observer()
            observer.schedule(log_handler, path = log_path)
            observer.start()
            print ('Started observer. ')
        except: 
            import traceback
            traceback.print_exc()

    def get_messages(self, from_date, to_date):
        messages = [x for x in self.messages if from_date < dateutil.parser.parse(x['timestamp']).replace(tzinfo = None) <= to_date]
        return messages

    def check_origin(self, origin): 
        return True

    @tornado.gen.coroutine
    def on_message(self, message): 
        try:
            message = json.loads(message)
        except: 
            self.write_message('Error converting message from json; probably not formatted correctly. Message was : ', message)
            raise tornado.gen.Return(None)

        try:
            from_date = message.get('from_date')
            date_format = '%Y-%m-%d'
            if from_date:
                from_date = datetime.datetime.strptime(from_date, date_format)
            else: 
                from_date = datetime.datetime.now() + dateutil.relativedelta.relativedelta(days = -2)

            to_date = message.get('to_date')
            if to_date: 
                to_date = datetime.datetime.strptime(to_date, date_format)
            else: 
                to_date = datetime.datetime.now()

            messages = self.get_messages(from_date, to_date)
            messages = {'type' : 'init', 'logs' : messages}
            self.write_message(json.dumps(messages))

        except: 
            import traceback
            traceback.print_exc()
