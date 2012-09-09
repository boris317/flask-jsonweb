import sys
from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.jsonweb import (
    JsonWeb, encode, decode, schema
)


app = Flask("widget")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

db = SQLAlchemy(app)     
jw = JsonWeb(app)


colors = db.Table('widget_colors',
    db.Column('color_id', db.Integer, db.ForeignKey('color.id')),
    db.Column('widget_id', db.Integer, db.ForeignKey('widget.id'))
)


@encode.to_object()
@decode.from_object()
class Color(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    
    def __init__(self, name):
        self.name = name
    
    
@encode.to_object()
@decode.from_object()
class Widget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), unique=True)
    colors = db.relationship(Color, secondary=colors)

    def __init__(self, type, colors=None):
        self.type = type
        self.colors = colors
    

@app.route("/widget", methods=["POST"])
@jw.json_view(expects=Widget)
def create_widget():
    widget = request.json
    db.session.add(widget)
    db.session.commit()
    return {"status": "ok"}

@app.route("/widget/<int:widget_id>")
@jw.json_view()
def get_widget(widget_id):
    widget = Widget.query.get(widget_id)
    if not widget:
        abort(404)
    return widget

@app.route("/error")
def error():
    raise TypeError("Boom")

if __name__ == "__main__":
    app.run('localhost', 6543)
