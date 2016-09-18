import tornado.gen
import time
import json
import uuid
from pbkdf2 import crypt

# TODO: Check if the implementation of the `pbkdf2` lib is credible,
# and if the library is maintained and audited. May switch to bcrypt.

@tornado.gen.coroutine
def get_or_create_token(datastore, username):
    found = False
    try:
        token_doc = yield datastore.get('tokens/by_username/%s' % username)
        found = True
    except datastore.KeyNotFound:
        doc = {
            'token': uuid.uuid4().hex,
            'username': username
        }
        yield datastore.insert('tokens/by_username/%s' % username, doc)
        yield datastore.insert('tokens/by_token/%s' % doc['token'], doc)
        raise tornado.gen.Return(doc['token'])
    finally:
        if found:
            raise tornado.gen.Return(token_doc['token'])

@tornado.gen.coroutine
def is_token_valid(datastore, token):
    valid = True
    try:
        res = yield datastore.get('tokens/by_token/%s' % token)
    except datastore.KeyNotFound:
        valid = False

    if valid:
        valid = (res['username'] != '__invalid__')
    raise tornado.gen.Return(valid)


def auth_only(coroutine):
    @tornado.gen.coroutine
    def func(handler):
        token = handler.request.headers.get('Authorization', '')
        token = token.replace('Token ', '')
        is_valid = yield is_token_valid(handler.datastore, token)
        if not is_valid:
            handler.json({'error': 'bad_token'}, 401)
        else:
            yield coroutine(handler)
    return func

@tornado.gen.coroutine
def admin_login(handler):
    body = None

    try:
        body = json.loads(handler.request.body)
        username = body['username'].decode('utf8')
        password = body['password'].decode('utf8')
    except:
        handler.json({'error': 'bad_body'}, 400)

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
        token = yield get_or_create_token(handler.datastore, username)
        handler.json({'token': token})
    else:
        handler.json({'error': 'invalid_password'}, 401)

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
    token = yield get_or_create_token(datastore, username)
    raise tornado.gen.Return(token)

@tornado.gen.coroutine
def ldap_login(handler):
    pass
