from tornado.testing import AsyncHTTPTestCase, AsyncTestCase, gen_test
from tornado.ioloop import PeriodicCallback, IOLoop
from tornado.gen import sleep, coroutine, Return
import json
import logging

from . import datastore, server, config
from .api import login

class TestDataStore(datastore.DataStore):
    def __init__(self):
        self.memory = {}

    @coroutine
    def check_connection(self):
        raise Return(True)

    @coroutine
    def insert(self, doc_id, document):
        self.memory[doc_id] = document
        raise Return(True)

    @coroutine
    def update(self, doc_id, document):
        yield self.insert(doc_id, document)

    @coroutine
    def get(self, doc_id):
        doc = self.memory.get(doc_id, None)
        if doc is None:
            raise datastore.KeyNotFound(doc_id)
        else:
            raise Return(doc)

    @coroutine
    def delete(self, doc_id):
        logging.info('DELETE %s' % (doc_id))
        del self.memory[doc_id]
        raise Return(True)

class BaseTest(AsyncHTTPTestCase):
    def get_app(self):
        self.test_config = config.Config(datastore=TestDataStore())
        return server.get_app(self.test_config)
    
    @coroutine
    def fetch(self, url, *args, **kwargs):
        raise Return(yield self.http_client.fetch(self.get_url(url), *args, **kwargs))

    @coroutine
    def get_token():
        TEST_USER = 'some_admin'
        TEST_PASS = 'some_pass'
        
        
class TestApp(AsyncHTTPTestCase):
    def test_no_body(self):
        resp = self.fetch('/api/login', method='POST', body='')
        self.assertEqual(resp.code, 400)

    def test_good_body(self):
        body = {'username': 'a', 'password': 'a'}
        resp = self.fetch('/api/login', method='POST', body=json.dumps(body))
        self.assertEqual(resp.code, 401)

    @gen_test
    def test_good_login(self):
        good_user = 'some_user'
        good_pass = 'ddeOpxNll$x201119'
        from .api import login
        yield login.create_admin(self.test_config.datastore, good_user,
            good_pass)

        body = {'username': good_user, 'password': good_pass}
        resp = yield self.http_client.fetch(self.get_url('/api/login'), method='POST', body=json.dumps(body))
        self.assertEqual(resp.code, 200)
