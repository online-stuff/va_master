import unittest
import time
import sys
from va_api import APIManager
import warnings


class TestClass(unittest.TestCase):
#    api = APIManager(va_url='https://127.0.0.1/api',token='daeebbeddbc0471d8d7f5ae2e7b5429c', verify=False)
    api = APIManager(va_url='https://127.0.0.1:443', va_user='admin', va_pass='admin', verify=False)
    warnings = []



    def tearDown(self):
        if self.warnings: 
            print "\nWARNINGS ===================="
            warnings.warn('\n'.join(self.warnings))

    def test_states_stores(self):
        states = self.api.api_call('/states', method='get', data={})
        
        self.assertTrue(states['success'])
        required_keys = {'name', 'icon', 'dependency', 'version', 'path', 'description'}
        warning_keys = {'module', 'panels'}
        for s in states['data']:
            self.assertTrue(set(s.keys()).issuperset(required_keys))
            if not set(s.keys()).issuperset(warning_keys):
                warning_str = "Expected to see 'module' and 'panels' key in state " + s['name'] + " but didn't. "
                self.warnings.append(warning_str)

    def test_list_panels(self):
        panels = self.api.api_call('/panels', method='get', data={})

        self.assertTrue(panels['success'])

        for p in panels['data']: 
            required_keys = {'servers', 'panels', 'name', 'icon'}
            self.assertTrue(set(p.keys()).issuperset(required_keys))

    def test_list_providers(self):
        a = self.api.api_call('/providers/info', method='post', data={})
        print ('Info : -----------')
        print (a)
        self.assertTrue(a['success'])

    def test_list_vpn_users(self):
        a = self.api.api_call('/apps/vpn_users', method='get', data={})
        self.assertTrue(a['success'])

    def test_get_vpn_status(self):
        a = self.api.api_call('/apps/vpn_status', method='get', data={})
        self.assertTrue(a['success'])

    def test_add_provider(self):
        providers =  self.api.api_call('/providers/info', method='post', data={})

        init_step = self.api.api_call('/providers/new/validate_fields', method='post', data={"driver_id" : "openstack", "field_values" : {}, "step_index" : -1})
        self.assertFalse(init_step['data']['errors'])

        info_step = self.api.api_call('/providers/new/validate_fields', method='post', data={"driver_id" : "openstack", "field_values" : {"provider_name" : "va-os", "username" : "admin", "tenant" : "admin", "provider_ip" : "192.168.80.16:5000", "region" : "RegionOne", "password" : "zilxii4g2j", "location" : "Skopje"}, "step_index" : 0})
        self.assertFalse(info_step['data']['errors'])

        network_step = self.api.api_call('/providers/new/validate_fields', method='post', data={"driver_id" : "openstack", "field_values" : {"sec_group" : "default|26811978-5201-41e5-8860-f71607928114", "network" : "public|9bd9a1c4-c46d-4976-b5a8-41c6c670bef2"}, "step_index" : 1})
        self.assertFalse(network_step['data']['errors'])

        image_step = self.api.api_call('/providers/new/validate_fields', method='post', data={"driver_id" : "openstack", "field_values" : {"size" : "va-medium", "image" : "debian-jessie"}, "step_index" : 2})
        self.assertFalse(image_step['data']['errors'])


        new_providers = self.api.api_call('/providers/info', method='post', data={})
        diff_providers = [x for x in new_providers if x not in providers]
        self.assertNotEqual(len(providers['data']), len(new_providers['data']))

    def test_delete_provider(self):
        providers = self.api.api_call('/providers/info', method='post', data={})
        a = self.api.api_call('/providers/delete', method='post', data={"provider_name": "va-os"})
        new_providers = self.api.api_call('/providers/info', method='post', data={})
        self.assertNotEqual(len(providers['data']), len(new_providers['data']))

if __name__ == '__main__':
    print(len(sys.argv))
    print(sys.argv)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClass)
    unittest.TextTestRunner(verbosity=5).run(suite)
