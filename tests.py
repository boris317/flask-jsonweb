import unittest

from werkzeug.test import EnvironBuilder
from flask import Flask, request
from flask.ext.jsonweb import JsonWeb, JsonWebBadRequest, \
     JsonWebRequest, encode, decode, schema


def get_request(obj):
    builder = EnvironBuilder("/", data=encode.dumper(obj))
    builder.headers["content-type"] = "application/json" 
    return JsonWebRequest(builder.get_environ())


class TestJsonWebRequest(unittest.TestCase):
    
    def setUp(self):
                
        @encode.to_object()
        @decode.from_object()        
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        self.person_cls = Person
                
    def tearDown(self):
        decode._default_object_handlers.clear()
        
    def test_json_attribute(self):                        
        request = get_request(self.person_cls("bob", "smith"))        
        person = request.json
        self.assertIsInstance(person, self.person_cls)
        
    def test_validation_error(self):
        
        v = schema.validators
        
        class PersonSchema(schema.ObjectSchema):
            first_name = v.String()
            last_name = v.String()
    
        schema.bind_schema("Person", PersonSchema)
        
        request = get_request(self.person_cls(1, "smith"))    
        with self.assertRaises(JsonWebBadRequest) as c:
            person = request.json
            
        error = c.exception
        self.assertIn("Error validating object", str(error))
        self.assertEqual("Expected str got int instead.", str(error.extra["fields"]["first_name"]))
        
    def test_json_decode_error(self):
        
        request = get_request({"__type__": "foo"})
        with self.assertRaises(JsonWebBadRequest) as c:
            obj = request.json
            
        error = c.exception.get_body(request.environ)
        self.assertIn("Cannot decode object foo. No such object.", error)

        
class TestJsonWeb(unittest.TestCase):
    def setUp(self):
        
        @encode.to_object()
        @decode.from_object()        
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        self.person_cls = Person        
        
        app = Flask("test")
        #app.testing = True
        
        jw = JsonWeb(app)
        
        @app.route("/person", methods=["POST"])
        @jw.json_view(expects=Person)
        def test_view():
            request.json
            return "ok"
        
        @app.route("/person", methods=["GET"])
        @jw.json_view()
        def get_person():
            return Person("Bob", "Smith")

        @app.route("/error", methods=["GET"])
        @jw.json_view()
        def error_view():
            raise TypeError("Boom!")
            
        self.test_client = app.test_client()
            
    def tearDown(self):
        decode._default_object_handlers.clear()            
        
    def post(self, url, data):
        return self.test_client.post(url, data=encode.dumper(data), 
                                     content_type="application/json")
    
    def test_view_gets_decoded_instance(self):
        person = self.person_cls("Bob", "Smith")
        
        with self.test_client as c:
            res = c.post("/person", data=encode.dumper(person), content_type="application/json")
            self.assertIsInstance(request._get_current_object(), JsonWebRequest)            
            self.assertIsInstance(request.json, self.person_cls)
            
        self.assertEqual(res.status_code, 200)
            
    def test_validation_error_response_when_type_not_expected(self):
        """
        Test that a validation error response is returned if request.json
        returns an object that is not an instance of the class supplied to
        JsonWeb.expects.
        """

        res = self.post("/person", [1,2,3])
            
        self.assertEqual(res.status_code, 400)
        self.assertIn("Expected Person got list instead.", res.data)
        
    def test_validation_error_response(self):
        """
        Test that a validation error response is returned when
        object validation fails.
        """
        
        v = schema.validators
        class PersonSchema(schema.ObjectSchema):
            first_name = v.String()
            last_name = v.String()
            
        schema.bind_schema("Person", PersonSchema)
        
        res = self.post("/person", self.person_cls(1, "smith"))
        self.assertEqual(res.status_code, 400)
        self.assertIn("Expected str got int instead.", res.data)
        
    def test_jsonweb_error_response(self):
        
        res = self.post("/person", {"__type__": "Foo", "value": 42})
        
        self.assertEqual(res.status_code, 400)
        self.assertIn("Cannot decode object Foo. No such object.", res.data)
        
    def test_non_jsonweb_error_response(self):
        res = self.test_client.get("/error")
        self.assertEqual(res.status_code, 500)
        self.assertIn("Unhandled Exception.", res.data)
        
    def test_wrong_content_type_returns_error(self):
        res = self.test_client.post("/person", 
                                    data=encode.dumper(self.person_cls(1, "smith")))
        
        self.assertEqual(res.status_code, 400)
        
    def test_decorated_view_makes_json_response(self):
        res = self.test_client.get("/person")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "application/json")
        self.assertIn('"__type__": "Person"', res.data)
        self.assertIn('"first_name": "Bob"', res.data)
        self.assertIn('"last_name": "Smith"', res.data)
        
        


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(TestJsonWebRequest))
    s.addTest(unittest.makeSuite(TestJsonWeb))
    return s

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
