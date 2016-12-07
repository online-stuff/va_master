import tornado.gen
import time
import json
import uuid
import functools
import salt
from pbkdf2 import crypt

# TODO: Check if the implementation of the `pbkdf2` lib is credible,
# and if the library is maintained and audited. May switch to bcrypt.


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
def get_user_type(handler):
    token = handler.request.headers.get('Authorization', '')
    token = token.replace('Token ', '')

    for type in ['user', 'admin']: # add other types as necessary, maybe from datastore. 
        if is_token_valid(handler.datastore, token, type): 
            raise tornado.gen.Return(type)
    raise tornado.gen.Return(None)

@tornado.gen.coroutine
def is_token_valid(datastore, token, user_type = 'admin'):
    valid = True
    try:
        res = yield datastore.get('tokens/%s/by_token/%s' % (user_type, token))
    except datastore.KeyNotFound:
        raise tornado.gen.Return(False)

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
            is_valid = yield is_token_valid(handler.datastore, token)
            if not is_valid:
                handler.json({'error': 'bad_token'}, 401)
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
        body = json.loads(handler.request.body)
        username = body['username'].decode('utf8')
        password = body['password'].decode('utf8')
    except:
        handler.json({'error': 'bad_body'}, 400)

    if '@' in username: 
        yield ldap_login(handler)
        raise tornado.gen.Return()

    try:
        admins = yield handler.datastore.get('admins')
    except handler.datastore.KeyNotFound:
        handler.json({'error': 'no_admins'}, 401)
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
        handler.json({'token': token})
    else:
        handler.json({'error': 'invalid_password'}, 401)


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
        handler.json({'token' : token})
    else: 
        handler.json({'error' : 'Invalid login: ' + result}, 401)



