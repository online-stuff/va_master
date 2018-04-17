import unittest
import time
import sys
from va_api import APIManager
import warnings
from va_test_base import VATestClass

class VAUsersTests(VATestClass):
    def get_users(self):
        users = self.api.api_call('/panels/users', method = 'get', data = {})
        return users

    def test_users(self):
        users = self.get_users()
        self.assertTrue(users['success'])

        required_keys = ['user', 'functions', 'groups']
        self.handle_keys_in_set(users['data'], required_keys, data_id_key = 'user')

    def test_add_user(self):
        user_functions = ['apps/action', 'panels', 'apps/get_panel']
        group = {'name' : 'providers', 'functions' : [{'func_path' : 'providers'}]}
        new_user = {'user' : 'test_user', 'password' : 'test_password', 'user_type' : 'user', 'functions' : user_functions, 'groups' : [group['name']]}

        new_group = self.api.api_call('/panels/create_user_group', method = 'post', data = {'group_name' : group['name'], 'functions' : group['functions']})
        self.assertTrue(new_group['success'])

        new_user_api = self.api.api_call('/panels/create_user_with_group', method = 'post', data = new_user)
        self.assertTrue(new_user_api['success'])

        all_users = self.get_users()
        self.assertTrue(all_users['success'])
        all_users = all_users['data']
        self.assertIn(new_user['user'], [x['user'] for x in all_users])

        login = self.api.api_call('/login', method = 'post', data = {'username' : new_user['user'], 'password' : new_user['password']})
        self.assertTrue(login['success'])
        token = login['data']['token']

        panels = self.api.api_call('/panels', method = 'get', data = {}, token = token)
        self.assertTrue(panels['success'])

        providers = self.api.api_call('/providers', method = 'post', data = {}, token = token)
        self.assertTrue(providers['success'])

        #This should fail because the user does not have access to this function. 
        providers_info = self.api.api_call('/providers/info', method = 'post', data = {}, token = token)
        self.assertFalse(providers_info['success'])

        delete = self.api.api_call('/panels/delete_user', method = 'post', data = {'user' : new_user['user']})
        self.assertTrue(delete['success'])

        delete_group = self.api.api_call('/panels/delete_group', method = 'post', data = {'group_name' : group['name']})
        self.assertTrue(delete_group['success'])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(VAUsersTests)
    unittest.TextTestRunner(verbosity=5).run(suite)
