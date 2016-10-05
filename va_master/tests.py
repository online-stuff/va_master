from . import server, config
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase, gen_test
from tornado.ioloop import PeriodicCallback, IOLoop
from tornado.gen import sleep
import tornado.gen
import json
import logging

from . import datastore
class TestDataStore(datastore.DataStore):
    def __init__(self):
        self.memory = {}

    @tornado.gen.coroutine
    def check_connection(self):
        logging.info('CHECK CONNECTION => True')
        raise tornado.gen.Return(True)

    @tornado.gen.coroutine
    def insert(self, doc_id, document):
        logging.info('INSERT %s %s' % (doc_id, repr(document)))
        self.memory[doc_id] = document
        raise tornado.gen.Return(True)

    @tornado.gen.coroutine
    def update(self, doc_id, document):
        yield self.insert(doc_id, document)

    @tornado.gen.coroutine
    def get(self, doc_id):
        logging.info('GET %s' % doc_id)
        doc = self.memory.get(doc_id, None)
        if doc is None:
            raise datastore.KeyNotFound(doc_id)
        else:
            raise tornado.gen.Return(doc)

    @tornado.gen.coroutine
    def delete(self, doc_id):
        logging.info('DELETE %s' % (doc_id))
        del self.memory[doc_id]
        raise tornado.gen.Return(True)

class TestApp(AsyncHTTPTestCase):
    def get_app(self):
        self.test_config = config.Config(datastore=TestDataStore())
        return server.get_app(self.test_config)

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
