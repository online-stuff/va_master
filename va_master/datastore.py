from abc import ABCMeta, abstractmethod
import tornado.gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import json
import base64

class DataStore(object):
    """A DataStore is an abstract definition of a key-value store that can
    contain objects targeted by id, and it should support CRUD operations.
    It is used for storing app metadata, scheduling data and configuration."""
    __metaclass__ =  ABCMeta

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
    def insert(self, doc_id, document):
        document_json = json.dumps(document)
        req = HTTPRequest('%s/v1/kv/%s' % (self.path, doc_id), method='PUT',
            body=document_json)
        yield self.client.fetch(req)

    @tornado.gen.coroutine
    def update(self, doc_id, document):
        yield self.insert(doc_id, document)

    @tornado.gen.coroutine
    def get(self, doc_id):
        resp = yield self.client.fetch('%s/v1/kv/%s' % (self.path, doc_id))
        resp = json.loads(resp.body)[0]['Value']
        resp = json.loads(base64.b64decode(resp))
        raise gen.Return(resp)

    @tornado.gen.coroutine
    def delete(self, doc_id):
        req = HTTPRequest('%s/v1/kv/%s' % (self.path, doc_id), method='DELETE')
        yield self.client.fetch(req)
