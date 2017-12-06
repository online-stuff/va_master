import unittest
import time
import sys
from va_api import APIManager
import warnings
from va_test_base import VATestClass

class VAUsersTests(VATestClass):
    def test_users(self):
        users = self.api.api_call('/panels/users', method = 'get', data = {})
        self.assertTrue(users['success'])
        
        required_keys = ['user', 'functions', 'groups']
        self.handle_keys_in_set(users['data'], required_keys, data_id_key = 'user')



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(VAUsersTests)
    unittest.TextTestRunner(verbosity=5).run(suite)
