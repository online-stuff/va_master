import unittest
from url_handler import gather_paths

class TestAPIMethods():

    def __init__(self, token, base_url):
        self.base_url = base_url
        self.paths = gather_paths()
        self.token = token

    def test_api_endpoints(self):
        for method in ['get', 'post']: 
            functions = self.paths[method]
            for f in functions: 
                exec_f = raw_input('Execute ' + f + ' ? y/n\n')
                if exec_f != 'y': continue
                f_args = functions[f]['args']
                f_name = functions[f]['function']
                entered_args = []
                if f_args != []: 
                    entered_args = []
                    for arg in f_args: 
                        new_arg = raw_input('Enter value for : ' + arg + '.\n')
                        entered_args.append(new_arg)
                print 'Want to call : ', f_name, ' with args : ', entered_args
        self.assertTrue(True)


#class TestAPIMethods(unittest.TestCase):
#
#    def setUp(self, handler, token, base_url):
#        self.base_url = base_url
#        self.paths = gather_paths()
#        self.token = token
#        self.handler = handler
#
#    def test_non_args(self):
#        for method in ['get', 'post']: 
#            functions = self.handler.paths[method]
#            for f in functions: 
#                f_args = ['test_' + x for x in f['args']]
#                print 'Want to call : ', f['function'], ' with args : ', f_args
#        self.assertTrue(True)
#
#    def test_isupper(self):
#        self.assertTrue('FOO'.isupper())
#        self.assertFalse('Foo'.isupper())
#
#    def test_split(self):
#        s = 'hello world'
#        self.assertEqual(s.split(), ['hello', 'world'])
#        # check that s.split fails when the separator is not a string
#        with self.assertRaises(TypeError):
#            s.split(2)
#
#


