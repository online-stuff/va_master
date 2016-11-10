from . import server, config
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase, gen_test
from tornado.ioloop import PeriodicCallback, IOLoop
from tornado.gen import sleep
import json

class MyCase(AsyncTestCase):
    def greet(self):
        print('wazaaap')

    @gen_test
    def test_sth(self):
        my_app = server.get_app(config.Config())
        cb = PeriodicCallback(self.greet, 1000, self.io_loop)
        cb.start()
        #yield sleep(10000)

class TestApp(AsyncHTTPTestCase):
    def get_app(self):
        test_config = config.Config()
        return server.get_app(test_config)

    def test_no_body(self):
        resp = self.fetch('/api/login', method='POST', body='')
        self.assertEqual(resp.code, 400)

    def test_good_body(self):
        body = {'username': 'a', 'password': 'a'}
        resp = self.fetch('/api/login', method='POST', body=json.dumps(body))
        self.assertEqual(resp.code, 401)
