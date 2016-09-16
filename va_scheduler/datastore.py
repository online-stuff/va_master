from abc import ABCMeta, abstractmethod
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import json
import base64

class KeyNotFound(IOError):
    def __init__(self, doc_id):
        super(IOError, self).__init__('The DataStore doesn\'t have the ' + \
        'following doc_id: %s' % doc_id)
        self.doc_id = doc_id

class StoreError(Exception):
    def __init__(self, exc):
        """Parameters:
          exc - The internal exception that happened during Store transaction
        """
        super(Exception, self).__init__(str(exc))
        self.exc = exc

class DataStore(object):
    """A DataStore is an abstract definition of a key-value store that can
    contain objects targeted by id, and it should support CRUD operations.
    It is used for storing app metadata, scheduling data and configuration."""
    __metaclass__ =  ABCMeta
    KeyNotFound = KeyNotFound
    StoreError = StoreError

    @abstractmethod
    def check_connection(self): pass

    @abstractmethod
    def check_connection_sync(self): pass

    @abstractmethod
    def insert(self, doc_id, document): pass

    @abstractmethod
    def update(self, doc_id, document): pass

    @abstractmethod
    def get(self, doc_id): pass

    @abstractmethod
    def delete(self, doc_id): pass

class ConsulStore(DataStore):
    """A DataStore provided by Consul KV, that uses JSON for storage.
    Read more at: https://www.consul.io/docs/agent/http/kv.html"""
    def __init__(self, path='http://127.0.0.1:8500'):
        self.path = path
        self.client = AsyncHTTPClient()

    @tornado.gen.coroutine
    def check_connection(self):
        try:
            result = yield self.client.fetch('%s/' % self.path)
        except:
            raise tornado.gen.Return(False)
        raise tornado.gen.Return(result.body == 'Consul Agent')

    def check_connection_sync(self):
        return ioloop.IOLoop.instance().run_sync(check_connection)

    @tornado.gen.coroutine
    def insert(self, doc_id, document):
        document_json = json.dumps(document)
        req = HTTPRequest('%s/v1/kv/%s' % (self.path, doc_id), method='PUT',
            body=document_json)
        try:
            yield self.client.fetch(req)
        except tornado.httpclient.HTTPError as e:
            raise StoreError(e)

    @tornado.gen.coroutine
    def update(self, doc_id, document):
        try:
            yield self.insert(doc_id, document)
        except tornado.httpclient.HTTPError as e:
            raise StoreError(e)

    @tornado.gen.coroutine
    def get(self, doc_id):
        try:
            resp = yield self.client.fetch('%s/v1/kv/%s' % (self.path, doc_id))
            resp = json.loads(resp.body)[0]['Value']
            resp = json.loads(base64.b64decode(resp))
            raise tornado.gen.Return(resp)
        except tornado.httpclient.HTTPError as e:
            if e.code == 404:
                raise KeyNotFound(doc_id)
            else:
                raise StoreError(e)

    @tornado.gen.coroutine
    def delete(self, doc_id):
        try:
            req = HTTPRequest('%s/v1/kv/%s' % (self.path, doc_id), method='DELETE')
            yield self.client.fetch(req)
        except tornado.httpclient.HTTPError as e:
            raise StoreError(e)
