import tornado.gen
import time
import json
import uuid
import functools
import salt
from pbkdf2 import crypt

# TODO: Check if the implementation of the `pbkdf2` lib is credible,
# and if the library is maintained and audited. May switch to bcrypt.

def get_paths():
    paths = {
        'get' : {
        },
        'post' : {
            'login' : {'function' : user_login, 'args' : ['datastore_handler', 'username', 'password']},
            'new_user' : {'function' : create_user_api, 'args' : ['user', 'password', 'user_type']}
        }
    }
    return paths





@tornado.gen.coroutine
def get_or_create_token(datastore, username, user_type = 'admin'):
    found = False
    try:
        token_doc = yield datastore.get('tokens/%s/by_username/%s' % (user_type, username))
        found = True
    except datastore.KeyNotFound:
        doc = {
            'token': uuid.uuid4().hex,
            'username': username
        }
        yield datastore.insert('tokens/%s/by_username/%s' % (user_type, username), doc)
        yield datastore.insert('tokens/%s/by_token/%s' % (user_type, doc['token']), doc)
        raise tornado.gen.Return(doc['token'])
    finally:
        if found:
            raise tornado.gen.Return(token_doc['token'])

@tornado.gen.coroutine
def get_current_user(handler):
    token = handler.request.headers.get('Authorization', '')

    token = token.replace('Token ', '')    
 
    for t in ['user', 'admin']: # add other types as necessary, maybe from datastore. 
        token_valid = yield is_token_valid(handler.datastore, token, t)
        if token_valid: 
            user = yield handler.datastore.get('tokens/%s/by_token/%s' % (t, token))
            raise tornado.gen.Return({'username' : user['username'], 'type' : t})
    raise tornado.gen.Return(None)


@tornado.gen.coroutine
def get_user_type(handler):
    user = yield get_current_user(handler)
    if user: 
        raise tornado.gen.Return(user['type'])
    raise tornado.gen.Return(None)

@tornado.gen.coroutine
def is_token_valid(datastore, token, user_type = 'admin'):
    valid = True
    try:
        user_handle = 'tokens/%s/by_token/%s' % (user_type, token)
        res = yield datastore.get(user_handle)
    except datastore.KeyNotFound:
        raise tornado.gen.Return(False)
    except Exception as e: 
        import traceback
        traceback.print_exc()
    valid = (res['username'] != '__invalid__')
    raise tornado.gen.Return(valid)

#So far, one kwarg is used: user_allowed. 
def auth_only(*args, **kwargs):
    user_allowed = kwargs.get('user_allowed', False)

    def auth_only_real(routine):
        @tornado.gen.coroutine
        @functools.wraps(routine)
        def func(handler):
            token = handler.request.headers.get('Authorization', '')
            token = token.replace('Token ', '')

            user_type = yield get_user_type(handler)
            #user_type is None if the token is invalid
            if not user_type or (user_type == 'user' and not user_allowed): 
                raise tornado.gen.Return({'success': False, 'message' : 'No user with this token found. Try to log in again. '})
            else:
                yield routine(handler)
        return func

    #Decorators are trippy with arguments. If no kwargs are set, you return the real auth function, otherwise, you call it and return the resulting function. 
    if any(args): 
        return auth_only_real(*args)
    else: 
        return auth_only_real


@tornado.gen.coroutine
def create_user(datastore_handler, username, password, user_type = 'user'):
    user = yield datastore_handler.find_user(username)
    if user: 
        raise Exception('Username ' + username + ' is already taken ')
    crypted_pass = crypt(password)
    user = {
        'username': username,
        'password_hash': crypted_pass,
        'timestamp_created': long(time.time())
    }
    yield datastore_handler.create_user(user, user_type)
    token = yield get_or_create_token(datastore_handler.datastore, username, user_type = user_type)

    raise tornado.gen.Return(token)

@tornado.gen.coroutine
def create_user_api(handler, user, password, user_type = 'user'):
    token = yield create_user(handler.datastore_handler, user, password, user_type) 
    raise tornado.gen.Return(token)



@tornado.gen.coroutine
def user_login(datastore_handler, username, password):
    body = None
    try: 
        if '@' in username: 
            yield ldap_login(handler)
            raise tornado.gen.Return()


        account_info = yield datastore_handler.find_user(username)
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
        if crypt(password, pw_hash) == pw_hash:
            token = yield get_or_create_token(datastore_handler.datastore, username, user_type = account_info['user_type'])
            raise tornado.gen.Return({'token': token})
        raise Exception ("Invalid password: " + password) 

    except tornado.gen.Return:
        raise
    except: 
        import traceback
        traceback.print_exc()


@tornado.gen.coroutine
def ldap_login(handler):
    body = json.loads(handler.request.body)
    username = body['username'].decode('utf8')
    password = body['password'].decode('utf8')

    username, directory_name = username.split('@')
    cl = salt.client.LocalClient()
    result = cl.cmd(directory_name, 'samba.user_auth', [username, password])['nino_dir'] #TODO write user_auth
    
    if result['success']: 
        token = yield get_or_create_token(handler.datastore, username, user_type = result['user_type'])
        raise tornado.gen.Return({'token' : token})
    else: 
        raise tornado.gen.Return({'error' : 'Invalid login: ' + result}, 401)


