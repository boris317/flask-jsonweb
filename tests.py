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
            
        error = c.exception.get_body(request.environ)
        self.assertIn("Error validating object", error)
        self.assertIn("Expected str got int", error)
        
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
        app.testing = True
        
        jw = JsonWeb(app)
        
        @app.route("/person", methods=["POST"])
        @jw.expects(Person)
        def test_view():
            request.json
            return "ok"
            
        self.test_client = app.test_client()
            
    def tearDown(self):
        decode._default_object_handlers.clear()            
            
    def test_view_gets_decoded_instance(self):
        person = self.person_cls("Bob", "Smith")
        
        with self.test_client as c:
            res = c.post("/person", data=encode.dumper(person), content_type="application/json")
            self.assertIsInstance(request._get_current_object(), JsonWebRequest)            
            self.assertIsInstance(request.json, self.person_cls)
            
        self.assertEqual(res.status_code, 200)
            
    def test_validation_error_is_raised_when_type_not_expected(self):
        
        with self.test_client as c:
            res = c.post("/person", data="[1,2,3]", content_type="application/json")
            
        self.assertEqual(res.status_code, 400)
        self.assertIn("Expected Person got list instead.", res.data)
        

        
                            
def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(TestJsonWebRequest))
    s.addTest(unittest.makeSuite(TestJsonWeb))
    return s

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
        