from functools import wraps
from jsonweb import encode, decode, schema
from jsonweb.exceptions import JsonWebError

from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException

from flask.wrappers import Request, cached_property
from flask.exceptions import JSONBadRequest
from flask import Response, request, current_app


def jsonweb_response(obj, status_code=200, headers=None):
    return Response(encode.dumper(obj), status_code,
                    headers=headers, mimetype="application/json")


def _error_response(message, status_code, **extra):
    extra["message"] = message
    return jsonweb_response(extra, status_code)


def make_json_error(e):
    if not isinstance(e, HTTPException):
        return _error_response("Unhandled Exception.", 500)        
    if isinstance(e, JsonWebBadRequest):
        return _error_response(str(e), e.code, **e.extra)
    return _error_response(str(e), e.code)


class JsonWebBadRequest(JSONBadRequest):

    description = (
        'The browser (or proxy) sent a request that this server could not '
        'understand.'
    )
    
    def __init__(self, description=None, **extra):
        super(JsonWebBadRequest, self).__init__(description)
        self.extra = extra


class JsonWebRequest(Request):
    """
    Subclass of the Flask :class:`~Flask.Request` object
    with JSON functionality overridden.
    """
    @cached_property
    def json(self):
        if self.mimetype != 'application/json':
            # Should we be more specific here?
            raise JsonWebBadRequest
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

                


