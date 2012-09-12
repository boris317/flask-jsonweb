import sys
from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.jsonweb import JsonWeb, schema, encode, \
     decode, json_view
from sqlalchemy.ext.associationproxy import association_proxy


"""
.. sourcecode:: http

   POST http://localhost:6543/widget HTTP/1.1

   {
       "__type__": "Widget", 
       "name": "Foo",
       "things": [
           {
               "__type__": "Thing", 
               "id": 1, 
               "name": "biz"
           }, 
           {
               "__type__": "Thing", 
               "id": 2, 
               "name": "baz"
           }
       ]
   }
"""


app = Flask("widget")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

db = SQLAlchemy(app)     
JsonWeb(app)

import logging
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(logging.StreamHandler())


# DB Models

def to_object():
    # We have to suppress these arguments because they are not JSON encodable.
    return encode.to_object(suppress=["query", "query_class", "metadata"])

@to_object()
@decode.from_object()
class Thing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    widget_id = db.Column(db.Integer, db.ForeignKey('widget.id'))
    name = db.Column(db.String(32))
    
    def __init__(self, name):
        self.name = name

  
@to_object()        
@decode.from_object()
class Widget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    things = db.relationship(Thing)

    def __init__(self, name, things=None):
        self.name = name
        if things:
            self.things = things


# JsonWeb Schemas

v = schema.validators
class ThingSchema(schema.ObjectSchema):
    name = v.String(32)

class WidgetSchema(schema.ObjectSchema):
    name = v.String(max_len=80)
    things = v.List(v.EnsureType(Thing))
    
schema.bind_schema("Widget", WidgetSchema)
schema.bind_schema("Thing", ThingSchema)


# Views

@app.route("/widget", methods=["POST"])
@json_view(expects=Widget)
def create_widget():
    widget = request.json
    db.session.add(widget)
    db.session.commit()
    return {"status": "ok"}


@app.route("/widget/<int:widget_id>")
@json_view()
def get_widget(widget_id):
    widget = Widget.query.get(widget_id)
    if not widget:
        abort(404)
    return widget


if __name__ == "__main__":
    app.run('localhost', 6543)
