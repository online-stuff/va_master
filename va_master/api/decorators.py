import json
#import cerberus
from functools import wraps
from tornado.gen import coroutine, Return


def auth_only(fn):
    # A coroutine signature is a boolean that gets set on every function
    # that was processed by the tornado coroutine decorator.
    # We use it to detect if the function is already a coroutine.

    COROUTINE_SIGNATURE = '__tornado_coroutine__'

    if getattr(fn, COROUTINE_SIGNATURE, None) is None:
        # This function was not wrapped in a coroutine, but we can
        # fix this by making it a coroutine here.

        fn = coroutine(fn)
    @coroutine
    def validate_request_auth(handler):
        from . import login
        token = login.get_token_from_header(handler)
        is_valid = yield login.is_token_valid(handler.datastore, token)
        raise Return(is_valid)

    @wraps(fn)
    @coroutine
    def new_fn(handler, *args, **kwargs):
        auth_result = yield validate_request_auth(handler)
        if not auth_result:
            # The user can't access this coroutine/endpoint
            # We need to send a Not Authorized response
            handler.set_status(401)
            raise Return({'error': 'failed_login'})

        res = yield fn(handler, *args, **kwargs)
        raise Return(res)
    return new_fn

class SchemaData(object):
    pass

def schema_coroutine(json_schema):
    '''A decorator that validates the schema of request bodies using Cerberus.
    Info about schemas: http://docs.python-cerberus.org/en/stable/
    Example:
    @schema_coroutine({'type': 'sth'})
    def my_request(handler, schema_data, *args, **kwargs):
        ...'''
    cerb_validator = cerberus.Validator(json_schema)
    def decorator(fn):
        @wraps(fn)
        @coroutine
        def new_fn(handler, *args, **kwargs):
            try:
                body = json.loads(handler.request.body)
                is_body_good = cerb_validator.validate(body)
                schema_data = SchemaData()
                for (k, v) in body.items():
                    setattr(schema_data, k, v)
                if not is_body_good:
                    raise ValueError
                else:
                    coroutine_fn = coroutine(fn)
                    res = yield coroutine_fn(handler, schema_data,
                            *args, **kwargs)
                    raise Return(res)
            except ValueError:
                handler.set_status(400)
                raise Return({'error': 'bad_body'})
        return new_fn
    return decorator
