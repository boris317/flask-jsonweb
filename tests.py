import unittest

from werkzeug.test import EnvironBuilder
from flask.ext.jsonweb import JsonWebBadRequest, JsonWebRequest, encode, decode, schema


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
            
                
def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(TestJsonWebRequest))
    return s

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
        