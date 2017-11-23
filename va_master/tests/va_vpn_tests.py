import unittest
import time
import sys
from va_api import APIManager
import warnings
from va_test_base import VATestClass

class VAVPNTests(VATestClass):
    def test_list_vpn_users(self):
        a = self.api.api_call('/apps/vpn_users', method='get', data={})
        self.assertTrue(a['success'])

    def test_get_vpn_status(self):
        a = self.api.api_call('/apps/vpn_status', method='get', data={})
        self.assertTrue(a['success'])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(VAVPNTests)
    unittest.TextTestRunner(verbosity=5).run(suite)
