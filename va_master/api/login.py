import time
import json
import uuid
import functools
import salt
import traceback
import datetime
from pbkdf2 import crypt
from tornado.gen import coroutine, Return
from .decorators import schema_coroutine

# TODO: Check if the implementation of the `pbkdf2` lib is sound,
# and if the library is maintained and audited. May switch to bcrypt.

def get_endpoints():
    paths = {
        'get' : {
        },
        'post' : {
            'login' : login_endpoint,
            # 'new_user' : create_user_api
        }
    }
    return paths

def generate_token():
    return uuid.uuid4().hex

@coroutine
def get_or_create_token(datastore, username):
    try:
        tokens = yield datastore.list_subkeys('tokens')
    except datastore.KeyNotFound:
        tokens = []
    for tok in tokens:
        try:
            tok_res = yield datastore.get('tokens/{}'.format(tok))
            if tok_res['username'] == username:
                raise Return(tok)
        except datastore.KeyNotFound:
            continue

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
def create_user(datastore, username, password):
    '''Inserts a new user in the database and returns a valid
    token for authenticating that particular user.'''
    pw_hash = crypt(password)
    doc = {
        'username': username,
        'password_hash': pw_hash,
        'timestamp_created': long(time.time())
    }
    yield datastore.insert('users/{}'.format(username), doc)
    token = yield get_or_create_token(datastore, username)

    raise Return(token)

def cli_create_user(parsed_args, config):
    import tornado.ioloop
    @coroutine
    def _create_user():
        is_ok = yield config.datastore.check_connection()
        if not is_ok:
            raise RuntimeError('Can\'t connect to the master!')
        yield create_user(config.datastore, parsed_args.username,
                parsed_args.password)
    try:
        tornado.ioloop.IOLoop.instance().run_sync(_create_user)
    except:
        config.logger.error('An error occured during user creation!')
        traceback.print_exc()

@schema_coroutine({'username': {'type': 'string'}, 'password': {'type':
    'string'}})
def create_user_endpoint(handler, schema_data):
    username = schema_data.username
    password = schema_data.password
    tok = yield create_user(username, password)
    raise Return({'token': tok})

@schema_coroutine({'username': {'type': 'string'}, 'password': {'type': 'string'}})
def login_endpoint(handler, schema_data):
    username = schema_data.username
    password = schema_data.password
    try:
        users = yield handler.datastore.list_subkeys('users')
    except handler.datastore.KeyNotFound:
        users = []

    if username not in users:
        # User doesn't exist
        handler.set_status(401)
        raise Return({'error': 'failed_login'})

    try:
        this_user = yield handler.datastore.get('users/{}'.format(username))
    except handler.datastore.KeyNotFound:
        # This is a race condition case, which *can* happen if the user
        # gets deleted after the list_subkeys() query.
        handler.set_status(401)
        raise Return({'error': 'failed_login'})

    pw_hash = this_user['password_hash']
    if crypt(password, pw_hash) == pw_hash:
        # This is the valid password, and we are ready to create a token
        # and return it.

        token = yield get_or_create_token(handler.datastore, username)
        raise Return({'token': token})
    handler.set_status(401)
    raise Return({'error': 'failed_login'})
