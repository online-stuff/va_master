import unittest
import sys
print ('Importing api')
from va_master import api

from va_master.utils.va_api import APIManager
import warnings

va_pass = 'admin'

class VATestClass(unittest.TestCase):
#    api = APIManager(va_url='https://127.0.0.1/api',token='1a882c9e22c2462d95dcadb8a127bb8d', verify=False)
    warnings = []

    @staticmethod
    def set_password(password):
        global va_pass
        print ('Setting pass : ', password)
        va_pass = password

    def setUp(self):
        print ('Using pass ', va_pass)
        self.api = APIManager(va_url='https://127.0.0.1:443', va_user='admin', va_pass=va_pass, verify=False)

    def tearDown(self):
        if self.warnings: 
            print "\nWARNINGS\n================\n"
            warnings.warn('\n'.join(self.warnings))


    def handle_keys_in_set(self, data, required_keys, warning_keys = {}, data_id_key = ''):
        for d in data:
            self.assertTrue(set(d.keys()).issuperset(required_keys), msg = "Failed key test for " + d.get(data_id_key, str(d)) + " : " + str(d.keys()) + " don't contain " + str(required_keys))
            if not set(d.keys()).issuperset(warning_keys):
                warning_str = "Expected to see " + str(warning_keys) + " in " + d.get(data_id_key, str(d)) + " but didn't. "
                self.warnings.append(warning_str)
