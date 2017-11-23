import unittest
import time
import sys
from va_api import APIManager
import warnings
from va_test_base import VATestClass

class VAStatesTests(VATestClass):
    def test_states_stores(self):
        states = self.api.api_call('/states', method='get', data={})
        self.assertTrue(states['success'])
        required_keys = {'name', 'icon', 'dependency', 'version', 'path', 'description'}
        warning_keys = {'module', 'panels'}

        self.handle_keys_in_set(states['data'], required_keys, warning_keys, data_id_key = 'name')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(VAStatesTests)
    unittest.TextTestRunner(verbosity=5).run(suite)
