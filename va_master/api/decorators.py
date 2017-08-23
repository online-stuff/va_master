import cerberus
from functools import wraps
from tornado.gen import coroutine

class SchemaData(object):
    pass

def schema(json_schema):
    '''A decorator that validates the schema of request bodies using Cerberus.
    Info about schemas: http://docs.python-cerberus.org/en/stable/
    Example:
    @schema({'type': 'sth'})
    @coroutine
    def my_request(handler, schema_data, *args, **kwargs):
        ...'''
    v = cerberus.Validator(json_schema)
    def decorator(fn):
        @wraps(fn)
        @coroutine
        def new_fn(handler, *args, **kwargs):
            try:
                body = json.loads(handler.request.body)
                is_body_good = v.validate(body)
                schema_data = SchemaData()
                for (k, v) in body.items():
                    setattr(schema_data, k, v)
                if not is_body_good:
                    raise ValueError
                else:
                    yield fn(handler, schema_data, *args, **kwargs)
            except:
                raise Return({'error': 'bad_body'}, 400)
    return decorator
