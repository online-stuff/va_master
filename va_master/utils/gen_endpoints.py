import unittest, simplejson
from url_handler import gather_paths

#Not used currently; previously used for generating a json of all endpoints. 

class TestAPIMethods():

    def __init__(self, token, base_url, paths = None):
        self.base_url = base_url
        self.paths = gather_paths()
        self.token = token

    def generate_api_endpoints(self):
        print self.paths
        serialized_paths = {m : {f : {'args' : self.paths[m][f]['args'] for x in self.paths[m][f]} for f in self.paths[m]} for m in ['post', 'get']}
        serialized_paths = {m : self.paths[m].keys() for m in ['post', 'get']}

        with open('api_endpoints.json', 'w') as f: 
            f.write(simplejson.dumps(serialized_paths, indent = 4))

    def set_paths(self, paths): 
        print 'Setting paths to : ', paths
        self.paths = paths

