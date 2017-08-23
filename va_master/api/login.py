import time
import json
import uuid
import functools
import salt
import datetime
from pbkdf2 import crypt
from tornado.gen import coroutine, Return

# TODO: Check if the implementation of the `pbkdf2` lib is sound,
# and if the library is maintained and audited. May switch to bcrypt.

def get_endpoints():
    paths = {
        'get' : {
        },
        'post' : {
            'login' : user_login,
            'new_user' : create_user_api
        }
    }
    return paths

def generate_token():
    return uuid.uuid4().hex

@coroutine
def get_or_create_token(datastore, username):
    found = False
    try:
        tokens = yield datastore.list_subkeys('tokens')
    except datastore.KeyNotFound:
        tokens = []
    for tok in tokens:
        try:
            tok_res = yield datastore.get('tokens/{}'.format(tok))
            if tok_res['username'] == username:
                raise Return(tok)

    # If the coroutine hasn't returned by now,
    # We should create a new token.
    # TODO: Validate token expiry?

    new_token_doc = {
        'username': username,
        'created': str(datetime.datetime.now())
    }
    token_value = generate_token()
    yield datastore.insert('tokens/{}'.format(token_value), new_token_doc)
    raise Return(token_value)

@coroutine
def get_current_user(handler):
    token = handler.request.headers.get('Authorization', '')

    token = token.replace('Token ', '')
    print ('Token is : ', token)
    for type in ['user', 'admin']: # add other types as necessary, maybe from datastore. 
        token_valid = yield is_token_valid(handler.datastore, token, type)
        if token_valid: 
            user = yield handler.datastore.get('tokens/%s/by_token/%s' % (type, token))
            raise Return({'username' : user['username'], 'type' : type})
    raise Return(None)


@coroutine
def get_user_type(handler):
    user = yield get_current_user(handler)
    if user:
        raise Return(user['type'])
    raise Return(None)

@coroutine
def is_token_valid(datastore, token):
    try:
        all_tokens = yield datastore.list_subkeys('tokens')
    except datastore.KeyNotFound:
        all_tokens = []
    if token in all_tokens:
        # It could be a valid token, but we have to query it.
        try:
            token_response = yield datastore.get('tokens/{}'.format(token))
            raise Return(token_response)
        except datastore.KeyNotFound:
            raise Return(False)
    else:
        # This is definitely not a valid token & it doesn't exist.
        raise Return(False)

#So far, one kwarg is used: user_allowed. 
def auth_only(*args, **kwargs):
    user_allowed = kwargs.get('user_allowed', False)

    def auth_only_real(routine):
        @coroutine
        @functools.wraps(routine)
        def func(handler):
            token = handler.request.headers.get('Authorization', '')
            token = token.replace('Token ', '')

            user_type = yield get_user_type(handler)
            #user_type is None if the token is invalid
            if not user_type or (user_type == 'user' and not user_allowed): 
                raise Return({'success': False, 'message' : 'No user with this token found. Try to log in again. '})
            else:
                yield routine(handler)
        return func

    #Decorators are trippy with arguments. If no kwargs are set, you return the real auth function, otherwise, you call it and return the resulting function. 
    if any(args):
        return auth_only_real(*args)
    else:
        return auth_only_real


@coroutine
def create_user(datastore, username, password, user_type = 'user'):
    datastore_handle = user_type + 's' #Basically, make it plural (admin -> admins, user -> users)
    if len(username) < 1 or len(password) < 1:
        raise ValueError('Username and password must not be empty.')
    try:
        new_users = yield datastore.get(datastore_handle)
    except datastore.KeyNotFound:
        yield datastore.insert(datastore_handle, [])
        new_users = []
    crypted_pass = crypt(password)
    print ('Pass hash will be : ', crypted_pass)
    new_users.append({
        'username': username,
        'password_hash': crypted_pass,
        'timestamp_created': long(time.time())
    })
    yield datastore.insert(datastore_handle, new_users)
    token = yield get_or_create_token(datastore, username, user_type = user_type)

    raise Return(token)

@coroutine
def create_user_api(handler):
    token = yield create_user(handler.config.deploy_handler.datastore, handler.data['user'], handler.data['pass'])
    raise Return(token)


@coroutine
def user_login(handler):
    body = None
    try:
        try:
            body = json.loads(handler.request.body)
            username = body['username'].decode('utf8')
            password = body['password'].decode('utf8')
        except:
            raise Return({'error': 'bad_body'}, 400)

        if '@' in username: 
            yield ldap_login(handler)
            raise Return()

        for user_type in ['admin', 'user']:
            datastore_handle = user_type + 's'
            try:
                print ('Trying for : ', datastore_handle)
                users = yield handler.datastore.get(datastore_handle)
                print ('Users are : ', users)
            except handler.datastore.KeyNotFound:
                raise Return({'error': 'no_users: ' + datastore_handle}, 401)
                # TODO: handle this gracefully?
                raise Return()

            account_info = None
            for user in users:
                if user['username'] == username:
                    account_info = user 
                    break
            print ('Account info is : ', account_info)
            invalid_acc_hash = crypt('__invalidpassword__')
            if not account_info:
                # Prevent timing attacks
                account_info = {
                    'password_hash': invalid_acc_hash,
                    'username': '__invalid__',
                    'timestamp_created': 0
                }
            pw_hash = account_info['password_hash']
            print ('Password is : ', password)
            print ('PW hash is : ', pw_hash)
            print (crypt(password, pw_hash))
            if crypt(password, pw_hash) == pw_hash:
                token = yield get_or_create_token(handler.datastore, username, user_type = user_type)
                raise Return({'token': token})
        raise Return({'error': 'invalid_password'})

    except Return:
        raise
    except:
        import traceback
        traceback.print_exc()


@coroutine
def ldap_login(handler):
    body = json.loads(handler.request.body)
    username = body['username'].decode('utf8')
    password = body['password'].decode('utf8')

    username, directory_name = username.split('@')
    cl = salt.client.LocalClient()
    result = cl.cmd(directory_name, 'samba.user_auth', [username, password])['nino_dir'] #TODO write user_auth
    if result['success']:
        token = yield get_or_create_token(handler.datastore, username, user_type = result['user_type'])
        raise Return({'token' : token})
    else:
        raise Return({'error' : 'Invalid login: ' + result}, 401)



