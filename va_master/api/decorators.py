import json
import cerberus
from functools import wraps
from tornado.gen import coroutine, Return

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
                    yield coroutine_fn(handler, schema_data, *args, **kwargs)
            except ValueError:
                handler.set_status(400)
                raise Return({'error': 'bad_body'})
        return new_fn
    return decorator
