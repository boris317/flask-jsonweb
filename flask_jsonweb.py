from functools import wraps
from jsonweb import encode, decode, schema
from jsonweb.exceptions import JsonWebError

from flask.wrappers import Request, cached_property
from flask.exceptions import JSONHTTPException, BadRequest
from flask import request

class JsonWebBadRequest(JSONHTTPException, BadRequest):

    description = (
        'The browser (or proxy) sent a request that this server could not '
        'understand.'
    )
    
    def __init__(self, description, **extra):
        super(JsonWebBadRequest, self).__init__(description)
        self.extra = extra
        
    def get_body(self, environ):
        """
        Overrides :meth:`flask.exceptions.JSONHTTPException.get_body`
        """ 
        error = dict(description=self.get_description(environ))
        error.update(self.extra)
        return encode.dumper(error) 


class JsonWebRequest(Request):
    """
    Subclass of the Flask :class:`~Flask.Request` object
    with JSON functionality overridden.
    """
    @cached_property
    def json(self):
        if self.mimetype == 'application/json':
            request_charset = self.mimetype_params.get('charset')
            try:
                return decode.loader(self.data, encoding=request_charset)
            except schema.ValidationError, e:
                return self.on_json_validation_error(e)            
            except JsonWebError, e:
                return self.on_json_loading_failed(e)
            
    def on_json_loading_failed(self, e):
        raise JsonWebBadRequest(e.message)
    
    def on_json_validation_error(self, e):
        raise JsonWebBadRequest(e.message, fields=e.errors)
    

class JsonWeb(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.request_class = JsonWebRequest
        
    def expects(self, cls):
        def dec(func):
            @wraps(func)
            def wrapper(*args, **kw):
                with decode.ensure_type(cls):
                    return func(*args, **kw)
            return wrapper
        return dec

                


