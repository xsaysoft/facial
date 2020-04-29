#
#@KEVIN DataBase Module
#
from flask import Flask
from app import  db,ma
from marshmallow import Schema, fields, pre_load, validate,ValidationError
from datetime import datetime



class Face(db.Model):
    __tablename__ = 'faces'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.Integer, nullable=False)
    face_id = db.Column(db.String(100), nullable=True)
    face_encode = db.Column(db.LargeBinary, nullable=True)
    creation_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)


# Create A SCHEMA for Face  Marshmallow
class FaceSchema(ma.ModelSchema):
    class Meta:
        model = Face 
     


