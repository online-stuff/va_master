import tornado.gen
import json
import uuid
from pbkdf2 import crypt

# TODO: Check if the implementation of the `pbkdf2` lib is credible,
# and if the library is maintained and audited. May switch to bcrypt.

@tornado.gen.coroutine
def get_or_create_token(handler, username):
    try:
        token_doc = yield handler.datastore.get('tokens/by_username/%s' % username)
        raise tornado.gen.Return(token_doc['token'])
    except:
        doc = {
            'token': uuid.uuid4().hex,
            'username': username
        }
        yield handler.datastore.insert('tokens/by_username/%s' % username, doc)
        yield handler.datastore.insert('tokens/by_token/%s' % doc['token'], doc)
        raise tornado.gen.Return(doc['token'])

@tornado.gen.coroutine
def is_token_valid(handler, token):
    valid = True
    try:
        res = yield handler.datastore.get('tokens/by_token/%s' % token)
    except:
        valid = False

    raise tornado.gen.Return(valid)

@tornado.gen.coroutine
def admin_login(handler):
    body = None

    try:
        body = json.loads(handler.request.body)
    except:
        handler.json({'error': 'bad_body'}, 400)

    if 'username' not in body or 'password' not in body:
        handler.json({'error': 'bad_body'}, 400)

    try:
        admins = yield handler.datastore.get('admins')
    except:
        handler.json({'error': 'no_admins'}, 401)
        # TODO: handle this gracefully?
        raise tornado.gen.Return()

    username = body['username']
    password = body['password']

    account_info = None
    for admin in admins:
        if admin['username'] == username:
            account_info = admin
            break
    if not account_info:
        handler.json({'error': 'invalid_username'}, 401)
    else:
        pw_hash = account_info['password_hash']
        if crypt(password, pw_hash) == pw_hash:
            token = yield get_or_create_token(handler, username)
            handler.json({'token': token})
        else:
            handler.json({'error': 'invalid_password'}, 401)

@tornado.gen.coroutine
def ldap_login(handler):
    pass
