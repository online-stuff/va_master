import tornado.web
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from . import status, login, hosts, apps
import json
import importlib

# These modules will be imported and they will be given the chance to register URLs
API_MODULES = [
    'va_master.api.apps',
    'va_master.api.status',
    'va_master.api.hosts',
    'va_master.api.login'
]

class ApiHandler(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config
        self.get_endpoints = {} # dict in the form of {URL: callback, ...}
        self.post_endpoints = {} # dict in the form of {URL: callback, ...} 
        self.__load_modules()

    def __load_modules(self):
        for module_name in API_MODULES:
            module = importlib.import_module(module_name)
            module.initialize(self)
    
    def add_get_endpoint(self, url, callback):
        """Adds a new HTTP GET endpoint.
        Args:
            url (str): The URL that the endpoint is going to handle.
            callback (function): A function that is called when the endpoint is hit. 
        """
        self.get_endpoints[url] = callback

    def add_post_endpoint(self, url, callback):
        """Adds a new HTTP POST endpoint.
        Args:
            url (str): The URL that the endpoint is going to handle.
            callback (function): A function that is called when the endpoint is hit. 
        """
        self.post_endpoints[url] = callback
    
    @property
    def datastore(self):
        return self.config.datastore

    def json(self, obj, status=200):
        """Returns a JSON body to the client.
        Args:
            obj (dict|list): A JSON-serializable dictionary or list.
            status (int): A HTTP status code.
        """
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        self.write(json.dumps(obj))
        self.finish()

    @coroutine
    def get(self, path):
        callback = self.get_endpoints.get(path, None)
        if callback is None:
            self.json({'error': 'not_found'}, 404)
        else:
            yield callback(self)
    
    @coroutine
    def post(self, path):
        callback = self.post_endpoints.get(path, None)
        if callback is None:
            self.json({'error': 'not_found'}, 404)
        else:
            yield callback(self)
