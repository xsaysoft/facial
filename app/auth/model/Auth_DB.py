#
#@KEVIN DataBase Module
#
from flask import Flask
from app import  db,ma
from marshmallow import Schema, fields, pre_load, validate,ValidationError
from datetime import datetime



class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=True)
    full_name = db.Column(db.String(200), unique=True, nullable=True)
    password = db.Column(db.Text, nullable=True)
    pin = db.Column(db.Text, nullable=True)
    device_id = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float, nullable=True)
    log = db.Column(db.Float, nullable=True)
    photo = db.Column(db.String(100), nullable=True)
    level = db.Column(db.Integer, nullable=True)
    activation = db.Column(db.Integer, nullable=True)
    recovery_phone = db.Column(db.Integer, nullable=True)
    status= db.Column(db.Boolean,nullable=True)
    creation_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    
    


class UserAuth(db.Model):
    __tablename__ = 'userauths'
    id = db.Column(db.Integer, primary_key=True)
    biometric_status= db.Column(db.Boolean,nullable=True)
    fa2_status= db.Column(db.Boolean,nullable=True)
    pin_status= db.Column(db.Boolean,nullable=True)
    password_status= db.Column(db.Boolean,nullable=True)
    phone_verify_status= db.Column(db.Boolean,nullable=True)
    biometric_photo = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    user = db.relationship('User', backref=db.backref('userauths', lazy='dynamic' ))




class UserLog(db.Model):
    __tablename__ = 'userlogs'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float, nullable=True)
    log = db.Column(db.Float, nullable=True)
    log_status= db.Column(db.Boolean,nullable=False)
    log_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('userlogs', lazy='dynamic' ))



def must_not_be_blank(data):
    if not data:
        raise ValidationError("Data not provided.")


class UserSchema(ma.Schema):
    id = fields.Integer()
    phone = fields.Integer(required=True,validate=must_not_be_blank)
    username = fields.String()
    full_name = fields.String()
    password = fields.String()
    pin = fields.String()
    device_id = fields.String(required=True,validate=must_not_be_blank)
    photo = fields.String()
    activation_code = fields.String()
    recovery_phone = fields.Integer()
    status = fields.String()
    lat = fields.String()
    log = fields.String()

class UserAllSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
     
class UserAuthSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserAuth

class UserLogSchema(ma.Schema):
        model = UserLog
        id = fields.Integer()
        token = fields.String()
        lat = fields.Float()
        log = fields.Float()
        log_status= fields.Boolean()

