from functools import wraps
from jsonweb import encode, decode, schema
from jsonweb.exceptions import JsonWebError

from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException

from flask.wrappers import Request, cached_property
from flask.exceptions import JSONBadRequest
from flask import Response, request

def jsonweb_response(obj):
    return Response(encode.dumper(obj),
                    mimetype="application/json")

def make_json_error(e):
    
    error = {"message": str(e)}
    
    if isinstance(e, JsonWebBadRequest):
        error.update(e.extra)

    response = jsonweb_response(error)
    response.status_code = (e.code
                            if isinstance(e, HTTPException)
                            else 500)
    return response

class JsonWebBadRequest(JSONBadRequest):

    description = (
        'The browser (or proxy) sent a request that this server could not '
        'understand.'
    )
    
    def __init__(self, description, **extra):
        super(JsonWebBadRequest, self).__init__(description)
        self.extra = extra

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
        # Modified from http://flask.pocoo.org/snippets/83/
        for code in default_exceptions.iterkeys():
            app.error_handler_spec[None][code] = make_json_error
        
    def json_view(self, expects=None):
        def dec(func):
            @wraps(func)
            def wrapper(*args, **kw):
                with decode.ensure_type(expects):
                    return jsonweb_response(func(*args, **kw))
            return wrapper
        return dec

                


