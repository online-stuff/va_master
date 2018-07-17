import unittest
import time
import sys
from va_api import APIManager
import warnings
from va_test_base import VATestClass

class VAPanelsTests(VATestClass):
    def test_list_panels(self):
        panels = self.api.api_call('/panels', method='get', data={})

        self.assertTrue(panels['success'])

        required_keys = {'servers', 'panels', 'name', 'icon'}
        self.handle_keys_in_set(panels['data'], required_keys, data_id_key = 'name')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(VAPanelsTests)
    unittest.TextTestRunner(verbosity=5).run(suite)
