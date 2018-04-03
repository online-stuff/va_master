
import requests, json

class APIManager():
    def __init__(self, va_url, token = '', va_user = '', va_pass = '', mock = False, verify = True):
        self.base_url = va_url
        if 'api' not in self.base_url: 
            self.base_url += '/api'
        self.verify = verify

        headers = {'Content-type' : 'application/json'}
        url = self.base_url + '/login'
        self.mock = mock

        if mock: 
            self.token = 'placeholder'
        elif token: 
            self.token = token
        elif va_user and va_pass: 
            response = requests.post(url, data = json.dumps({'username' : va_user, 'password' : va_pass}), headers = headers, verify = False)
            self.token = response.json()['data']['token']
        else: 
            raise Exception('Cannot start va api: either the token or the va_user and va_pass should be set up properly. ')


    def api_call(self, url, data, method = 'get'):
        if self.mock: return self.mock_api_call(url, data, method)


        kwargs = {
            'get' : {'params' : data}, 
            'delete' : {'data' : json.dumps(data)},
            'post' : {'data' : json.dumps(data)}
        }[method]

        kwargs['url'] = self.base_url + url
        kwargs['headers'] = {'Content-type' : 'application/json', 'Authorization' : 'Token ' + self.token}
        kwargs['verify'] = self.verify

        response = getattr(requests, method)(**kwargs)
        if response.headers['Content-type'] == 'application/json': 
            result = response.json()
        else: 
            result = response.text
        # print ('Response is : ', response.text)
        return result

    def mock_api_call(self, url, data, method):
        url = self.base_url + url
        headers = {'Content-type' : 'application/json', 'Authorization' : 'Token ' + self.token}

        print ('Mock api call on ', url)
        print ('Data : ', data)
        print ('Headers : ', headers)
        return {'success' : True, 'message' : '', 'data' : {}}
