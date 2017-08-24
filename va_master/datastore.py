from abc import ABCMeta, abstractmethod
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.gen import coroutine, Return
import tornado.ioloop
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
        super(Exception, self).__init__(repr(exc))
        self.exc = exc

class DataStore(object):
    """A DataStore is an abstract definition of an async key-value store that
    can contain objects targeted by id, and it should support CRUD operations.
    It is used for storing app metadata, scheduling data and configuration."""
    __metaclass__ =  ABCMeta
    KeyNotFound = KeyNotFound
    StoreError = StoreError

    @abstractmethod
    @coroutine
    def check_connection(self): pass

    @abstractmethod
    @coroutine
    def insert(self, doc_id, document): pass

    @abstractmethod
    @coroutine
    def update(self, doc_id, document): pass

    @abstractmethod
    @coroutine
    def get(self, doc_id): pass

    @abstractmethod
    @coroutine
    def delete(self, doc_id): pass

class ConsulStore(DataStore):
    """A DataStore provided by Consul KV, that uses JSON for storage.
    Read more at: https://www.consul.io/docs/agent/http/kv.html"""
    def __init__(self, path='http://127.0.0.1:8500'):
        self.path = path
        self.client = AsyncHTTPClient()

    @coroutine
    def check_connection(self):
        try:
            result = yield self.client.fetch('%s/v1/status/leader' % self.path)
        except:
            raise Return(False)
        raise Return(result.code == 200 and result.body != '""')

    @coroutine
    def insert(self, doc_id, document):
        document_json = json.dumps(document)
        req = HTTPRequest('%s/v1/kv/%s' % (self.path, doc_id), method='PUT',
            body=document_json)
        try:
            yield self.client.fetch(req)
        except Exception as e:
            raise StoreError(e)

    @coroutine
    def update(self, doc_id, document):
        try:
            yield self.insert(doc_id, document)
        except Exception as e:
            raise StoreError(e)

    @coroutine
    def __get_helper(self, doc_id):
        '''This is a helper method to get a document that does the
        network call, but doesn't do any processing.'''

        is_ok = False
        try:
            resp = yield self.client.fetch('%s/v1/kv/%s' % (self.path, doc_id))
            resp = json.loads(resp.body)
            is_ok = True
        except tornado.httpclient.HTTPError as e:
            if e.code == 404:
                raise KeyNotFound(doc_id)
            else:
                raise StoreError(e)
        except Exception as e:
            raise StoreError(e)
        if is_ok:
            raise Return(resp)

    @coroutine
    def get(self, doc_id):
        resp = yield self.__get_helper(doc_id)
        resp = resp[0]['Value']
        resp = json.loads(base64.b64decode(resp))
        raise Return(resp)

    @coroutine
    def list_subkeys(self, key):
        res = yield self.__get_helper('{}?keys'.format(key))
        if res:
            def filter_key(c_key):
                '''The response is in the format ['key/a', 'key/b', 'key/c']
                but we want ['a', 'b', 'c'], so we filter the prefix.'''
                prefix = key
                if prefix[-1] != '/': prefix+= '/'
                return c_key.replace(prefix, '', 1)
            res = [filter_key(x) for x in res]
        raise Return(res)

    @coroutine
    def delete(self, doc_id):
        try:
            req = HTTPRequest('%s/v1/kv/%s' % (self.path, doc_id), method='DELETE')
            yield self.client.fetch(req)
        except Exception as e:
            raise StoreError(e)
