import unittest
import time
import sys
from va_api import APIManager
import warnings
from va_test_base import VATestClass

class VAServicesTests(VATestClass):
    def test_services(self):
        services = self.api.api_call('/services', method='get', data={})
        self.assertTrue(services['success'])
    
    def test_presets(self):
        presets = self.api.api_call('/services/get_service_presets')
        new_service = {'presets' : ['ping_preset'], 'server' : 'va-master', 'name' : 'test_preset', 'address' : '127.0.0.1', 'port' : '443', 'tags' : 'test'}

        result = self.api.api_call('/services/add_service_with_presets', data = new_service, method = 'post')
        print 'adding ', result

        all_checks = self.api.api_call('/services/get_services_with_checks')
        print all_checks['data'].keys()
        self.assertTrue(all_checks['success'])
        services = all_checks['data'].keys()
        self.assertIn(new_service['name'], services)

        result = self.api.api_call('/services/delete', data = {'name' : new_service['name']}, method = 'delete')
        print result

        all_checks = self.api.api_call('/services/get_services_with_checks')

        self.assertTrue(all_checks['success'])
        services = all_checks['data'].keys()
        self.assertNotIn(new_services['name'], services)


        

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(VAServicesTests)
    unittest.TextTestRunner(verbosity=5).run(suite)
