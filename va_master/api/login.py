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
            'login' : user_login, 
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
#    print ('Token is : ', token)
    
    for type in ['user', 'admin']: # add other types as necessary, maybe from datastore. 
        token_valid = yield is_token_valid(handler.datastore, token, type)
        if token_valid: 
            user = yield handler.datastore.get('tokens/%s/by_token/%s' % (type, token))
            raise tornado.gen.Return({'username' : user['username'], 'type' : type})
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
        res = yield datastore.get('tokens/%s/by_token/%s' % (user_type, token))
    except datastore.KeyNotFound:
        raise tornado.gen.Return(False)
    except Exception as e: 
        print ('Something weird happened. ')
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
def create_admin(datastore, username, password):
    if len(username) < 1 or len(password) < 1:
        raise ValueError('Username and password must not be empty.')
    try:
        new_admins = yield datastore.get('admins')
    except datastore.KeyNotFound:
        yield datastore.insert('admins', [])
        new_admins = []
    new_admins.append({
        'username': username,
        'password_hash': crypt(password),
        'timestamp_created': long(time.time())
    })
    yield datastore.insert('admins', new_admins)
    token = yield get_or_create_token(datastore, username, user_type = 'admin')

    raise tornado.gen.Return(token)


@tornado.gen.coroutine
def user_login(handler):
    body = None
    try: 
        try:
            body = json.loads(handler.request.body)
            username = body['username'].decode('utf8')
            password = body['password'].decode('utf8')
        except:
            raise tornado.gen.Return({'error': 'bad_body'}, 400)

        if '@' in username: 
            yield ldap_login(handler)
            raise tornado.gen.Return()

        try:
            admins = yield handler.datastore.get('admins')
        except handler.datastore.KeyNotFound:
            raise tornado.gen.Return({'error': 'no_admins'}, 401)
            # TODO: handle this gracefully?
            raise tornado.gen.Return()

        account_info = None
        for admin in admins:
            if admin['username'] == username:
                account_info = admin
                break
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
            token = yield get_or_create_token(handler.datastore, username, user_type = 'admin')
            raise tornado.gen.Return({'token': token})
        else:
            raise tornado.gen.Return({'error': 'invalid_password'}, 401)

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



