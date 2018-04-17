import unittest
import time
import sys
from va_api import APIManager
import warnings
from va_test_base import VATestClass

class VAUsersTests(VATestClass):
    def get_users(self):
        users = self.api.api_call('/panels/users', method = 'get', data = {})
        self.assertTrue(users['success'])

        return users

    def check_if_user_exists(self, user):
        users = self.get_users()
        self.assertIn(user['user'], [x['user'] for x in users['data']])

    def test_users(self):
        users = self.get_users()
        self.assertTrue(users['success'])

        required_keys = ['user', 'functions', 'groups']
        self.handle_keys_in_set(users['data'], required_keys, data_id_key = 'user')

    def add_group(self, group):
        new_group = self.api.api_call('/panels/create_user_group', method = 'post', data = {'group_name' : group['name'], 'functions' : group['functions']})
        self.assertTrue(new_group['success'])

    def add_user(self, user)       :
        new_user_api = self.api.api_call('/panels/create_user_with_group', method = 'post', data = user)
        self.assertTrue(new_user_api['success'])

    def _test_user_endpoint(self, function, token = '', method = 'get', data = {}, success = True):
        result = self.api.api_call(function, method = method, data = data, token = token)
        self.assertEqual(result['success'], success)

    def test_add_user(self):
        user_functions = ['apps/action', 'panels', 'apps/get_panel']
        group = {'name' : 'providers', 'functions' : [{'func_path' : 'providers'}]}
        new_user = {'user' : 'test_user', 'password' : 'test_password', 'user_type' : 'user', 'functions' : user_functions, 'groups' : [group['name']]}

        self.add_group(group)
        self.add_user(new_user)
        self.check_if_user_exists(new_user)

        login = self.api.api_call('/login', method = 'post', data = {'username' : new_user['user'], 'password' : new_user['password']})
        self.assertTrue(login['success'])
        token = login['data']['token']

        panels = self._test_user_endpoint('/panels', method = 'get', token = token)
        providers = self._test_user_endpoint('/providers', method = 'post', token = token)
        #This should fail because the user does not have access to this function. 
        providers_info = self._test_user_endpoint('/providers/info', method = 'post', token = token, success = False)

        delete = self.api.api_call('/panels/delete_user', method = 'post', data = {'user' : new_user['user']})
        self.assertTrue(delete['success'])

        delete_group = self.api.api_call('/panels/delete_group', method = 'post', data = {'group_name' : group['name']})
        self.assertTrue(delete_group['success'])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(VAUsersTests)
    unittest.TextTestRunner(verbosity=5).run(suite)
