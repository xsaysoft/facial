from flask import Flask ,request,Response
from app.auth.model import SECRET_KEY ,auth,authToken
from functools import wraps
import jwt,secrets,datetime
from urllib.parse import urlencode, quote_plus
from passlib.apps import custom_app_context as pwd_context



#
# Protecting route jwt 
#
def token_required(f):
    @wraps(f)
    def decorated(current_data,*args, **kwargs):
        token=None
        if 'appmart-token' in request.headers:
            token =request.headers['appmart-token']
        
        if not  token:
            return  {'status': "error","data": {"code":500,"message": "Token is missing."}}, 200
           
        try:
            current_data=jwt.decode(token,SECRET_KEY,algorithm='HS256')

        except jwt.ExpiredSignatureError:
               return  {'status': "error","data": {"code":501,"message": "Token expired. Get new one."}}, 200
        except jwt.InvalidSignatureError:
               return  {'status': "error","data": {"code":503,"message": "Token’s signature doesn’t match . "}}, 200
        except jwt.DecodeError:
               return  {'status': "error","data": {"code":503,"message": "token cannot be decoded because it failed validation."}}, 200

        return f(current_data,*args,**kwargs)
    return decorated


#
# Password Hashing @password using  PassLib for password hashing
#
def token_decode():
    if 'appmart-token' in request.headers:
        token =request.headers['appmart-token']
        if not  token:
            return  {'status': False,"data": {"code":107,"message": "Token is missing ."}}, 400 
        try:
            current_data=jwt.decode(token,SECRET_KEY,algorithm='HS256')
        except:
             return  {'status': False,"data": {"code":101,"message": "Invalid Token"}}, 401
        return current_data



#
# Password Hashing @password using  PassLib for password hashing
#
def hash_password( password):
       return pwd_context.encrypt(password)

#
# Verify password  @password , @password_hash verify password hashing
#
def verify_password(password_hash, password):
        return pwd_context.verify(password, password_hash)

