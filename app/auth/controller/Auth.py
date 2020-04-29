#
#@KEVIN Authentication module for registartion , login, validation , splashscreen, token Resend 
#
from flask import request
from flask_restful import Resource
from app.auth.model.Auth_DB import db, User, UserSchema ,UserAllSchema, UserAuth, UserAuthSchema, UserLog, UserLogSchema
from app.auth.service.resource import random_gentarted,save_changes ,verify_expire_code
from app.auth.util.token import token_required,SECRET_KEY,auth,hash_password ,verify_password as veri_pass,token_decode
import jwt,json,secrets,datetime
from marshmallow import ValidationError, post_load
from sqlalchemy import or_, and_



users_schema = UserAllSchema(many=True)
user_schema = UserSchema()
userlog_schema =UserLogSchema()
user_all_schema = UserAllSchema()



#
#password verify
#
@auth.verify_password
def verify_password(phone, password):
    user = User.query.filter_by(phone = phone).first()
    if not user or not veri_pass(user.password,password):
       return False
    user = user
    return True

@auth.error_handler
def auth_error():
     return  {'status': "error","data": {"code":202,"message": "Invalid Login details"}}, 200
#
#welcome page  
#
class HomeResource(Resource):
    def get(self):
        return {"Facial Biometric API"}, 200

#
#Registartion @phone,@device_id 
#

class RegResource(Resource):
    
    def get(self):
        users = User.query.all()
        users = users_schema.dump(users)
        return {'status': 'success', 'data': users}, 200

    def post(self):
        verify_code = verify_expire_code["code"]= random_gentarted(4) 
        json_data = request.get_json(force=True)
        if not json_data:
            return  {'status': "error","data": {"code":107,"message": "No input data provided"}}, 400
        try:
            data = user_schema.load(json_data)
        except ValidationError as err:
            return  {'status': "error","data": {"code":107,"message": err.messages }}, 400

        if not data['phone']:
            return  {'status': "error","data": {"code":107,"message": "Empty (Phone) field."}}, 400

        user = User.query.filter_by(phone=data['phone'],device_id=data['device_id'],status = True).first()
        if  user:
             return  {'status': "success","data": {"code":103,"message":'User already exists'}}, 200
        
        user = User.query.filter(or_(User.phone==data['phone'],User.device_id=='missing'),User.status == True).first()
        if  user:
            return  {'status': "success","data": {"code":104,"message":'Activated phone number found'}}, 200

        user = User.query.filter(or_(User.phone=='missing',User.device_id==data['device_id']),User.status == True).first()
        if  user:
            return  {'status': "success","data": {"code":104,"message":'Activated Device ID found'}}, 200

        user = User.query.filter(or_(User.phone==data['phone'],User.device_id==data['device_id'],User.status == False)).first()
        if not user:
            user = User(phone=data['phone'],device_id=data['device_id'],activation=verify_code,level=0)
            save_changes(user)
            #remove verify_code on production
            return  {'status': "success","data": {"code":100,"verify_code": verify_code}}, 201
        else:
            user_verify = User.query.filter_by(phone=data['phone']).first()
            user = User.query.filter(or_(User.phone==data['phone'],User.device_id!=data['device_id']),User.status == None).first()
            if  user:
                if user.level==0:
                   level=user.level
                elif user.activation==1:
                    level=1
                elif user.level==1:
                    level=0
                else:
                    level=user.level
                user_verify.activation=verify_code
                user.device_id=data['device_id']
                db.session.commit()
                 #remove verify_code on production
                return  {'status': "success","data": {"code":102,"message":'Phone number found',"level":level,"verify_code": verify_code}}, 200

            user = User.query.filter(or_(User.phone!=data['phone'],User.device_id==data['device_id']),User.status == None).first()
            if  user:
                if user.level==0:
                   level=user.level
                elif user.activation==1:
                    level=1
                elif user.level==1:
                    level=0
                else:
                    level=user.level
                user.activation=verify_code
                db.session.commit()
                 #remove verify_code on production
                return  {'status': "success","data": {"code":102,"message":'Device ID found!!',"level":level,"verify_code": verify_code}}, 200

            

        
    #
    #Update User Data
    #
    def put(self):
        verify_code = verify_expire_code["code"]= random_gentarted(4) 
        json_data = request.get_json(force=True)
        if not json_data:
               return  {'status': "error","data": {"code":107,"message": "No input data provided"}}, 400
        try:
            data = user_schema.load(json_data)
        except ValidationError as err:
            return  {'status': "error","data": {"code":107,"message": err.messages }}, 400 

        user = User.query.filter_by(phone=data['phone'],device_id=data['device_id']).first()
        if not user:
            return  {'status': "error","data": {"code":102, "message":'User does not exist' }}, 200
        user.activation=verify_code
        user =data
        db.session.commit()
    
        return  {'status': "success","data": {"code":100,"message":'successful',"verify_code": verify_code}}, 200
     
    #
    #Delete Data
    #
    def delete(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return  {'status': "error","data": {"code":107,"message": "No input data provided"}}, 400
        try:
            data = user_schema.load(json_data)
        except ValidationError as err:
            return  {'status': "error","data": {"code":107,"message": err.messages }}, 400  

        user= User.query.filter_by(phone=data['phone']).delete()
    
        if not user:
            return  {'status': "error","data": {"code":102, "message":'User does not exist' }}, 200
        db.session.commit()
        return  {'status': "success","data": {"code":100,"message":'User data has been deleted'}}, 200
       


#
#Validation @phone,@device_id,@activation_code
#
class ValidateResource(Resource):

    def put(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return  {'status': "error","data": {"code":107,"message": "No input data provided"}}, 400
       
        try:
            data = user_schema.load(json_data)
        except ValidationError as err:
            return  {'status': "error","data": {"code":107,"message": err.messages }}, 400 

        

        if not 'activation_code' in request.json:
            return  {'status': "error","data": {"code":107,"message": "Missing (activation_code) field."}}, 400 

        user = User.query.filter_by(phone=data['phone'],device_id=data['device_id'],activation=data['activation_code']).first()
        if not user:
            return  {'status': "error","data": {"code":102,"message": "activation code does not match."}}, 200 
            
        validCode= verify_expire_code.get('code')
        if not validCode:
            return  {'status': "error","data": {"code":102,"message": "activation code has expired."}}, 200
        user.level=1
        user.activation =1
        db.session.commit()
        return  {'status': "success","data": {"code":100,"message":'activation successful'}}, 200
       

#
#Password Check @phone,@device_id 
#
class PasswordSetResource(Resource):
    
    def put(self):
        json_data = request.get_json(force=True)
        if not json_data:
               return  {'status': "error","data": {"code":107,"message": "No input data provided." }}, 400
        try:
            data = user_schema.load(json_data)
        except ValidationError as err:
            return  {'status': "error","data": {"code":107,"message": err.messages }}, 400  

        if not 'password' in request.json:
            return  {'status': "error","data": {"code":107,"message": "Missing (password field.)"}}, 400

        if not 'recovery_phone' in request.json:
            return  {'status': "error","data": {"code":107,"message": "Missing (recovery_phone.)"}}, 400

        user = User.query.filter_by(phone=data['phone'],device_id=data['device_id']).first()
        if not user:
            return  {'status': "success","data": {"code":102,"message": "phone details does not match ."}}, 200 
        
        user.password =hash_password(data['password'])
        user.recovery_phone=data['recovery_phone']
        user.status = True
        db.session.commit()
        
        token=jwt.encode({'phone': user.phone,'password': user.password,'full_name': user.full_name, 'device_id': user.device_id,'exp' : datetime.datetime.utcnow()+ datetime.timedelta(minutes=1000)},SECRET_KEY,algorithm='HS256')
        return { "status": 100, "data": {'message': 'password set was successful','token':token.decode('UTF-8')}}, 200

#
#SplachSscreen @phone,@device_id 
#

class SplashSetResource(Resource):
   
    def post(self):
       
        json_data = request.get_json(force=True)
        if not json_data:
               return  {'status': "error","data": {"code":107,"message": "No input data provided." }}, 400
   
        data = json_data
        if not 'device_id' in request.json:
            return  {'status': "error","data": {"code":107,"message": "Missing (device_id) field."}}, 400 

        user = User.query.filter_by(device_id=data['device_id']).first()
        if not user:
            return  {'status': "success","data": {"code":101,"message": "Device id does not match ."}}, 200 
            
        if 'appmart-token' in request.headers:
            token =request.headers['appmart-token']
            try:
                current_data=jwt.decode(token,SECRET_KEY,algorithm='HS256')
            except:
                return  {'status': "success","data": {"code":101,"message": "Invalid Token Detail ."}}, 200 
            user = User.query.filter_by(phone=current_data['phone'],device_id=current_data['device_id']).first()
            if user:
                token=jwt.encode({'phone': user.phone,'password': user.password,'full_name': user.full_name, 'device_id': user.device_id,'exp' : datetime.datetime.utcnow()+ datetime.timedelta(minutes=1000)},SECRET_KEY,algorithm='HS256')
                return  {'status': "success","data": {"code":100,"message": "Login successful",'token':token.decode('UTF-8')}}, 200

            user = User.query.filter(or_(User.phone=='missing',User.device_id==current_data['device_id'])).first()
            if  user:
                return  {'status':"success","data": {"code":103,"message": "Error you already login to another device."}}, 200 
            user = User.query.filter(or_(User.phone==current_data['phone'],User.device_id=='missing')).first()
            if  user:
                return  {'status':"success","data": {"code":103,"message": "Error you already login to another device."}}, 200
       
        return  {'status': "success","data": {"code":102,"message": "Invalid login details ."}}, 200
        

#
#Login R-@phone , R-@device_id, @lat,@log 
#
class LoginSetResource(Resource):
    @auth.login_required
    def post(self):
        json_data = request.get_json(force=True)
        if not json_data:
               return  {'status': "error","data": {"code":107,"message": "No input data provided." }}, 400
   
        try:
            data = user_all_schema.load(json_data)
        except ValidationError as err:
            return  {'status': "error","data": {"code":107,"message": err.messages }}, 400 

        user = User.query.filter_by(phone=data['phone'],device_id=data['device_id']).first()
        if user:
            token=jwt.encode({'phone': user.phone,'password': user.password,'full_name': user.full_name, 'device_id': user.device_id,'exp' : datetime.datetime.utcnow()+ datetime.timedelta(minutes=1000)},SECRET_KEY,algorithm='HS256')
          
            userlog = UserLog.query.filter_by(user_id=user.id).first()
            if not userlog:
               user = UserLog(token=token.decode('UTF-8'),user_id=user.id,log_status=1)
               save_changes(user)
            else:
                if not 'lat' in json_data and not 'log' in json_data:
                    userlog.token =token.decode('UTF-8')
                    userlog.log_status=True
                    db.session.commit()
                else:
                    userlog.lat=data['lat']
                    userlog.log=data['log']
                    userlog.token =token.decode('UTF-8')
                    userlog.log_status=True
                    db.session.commit()
            
            return  {'status': "success","data": {"code":100,"message": "Login successful",'token':token.decode('UTF-8')}}, 200
            
        user = User.query.filter(or_(User.phone=='missing',User.device_id==data['device_id'])).first()
        if  user:
            return  {'status': "error","data": {"code":101,"message": "Error you already login to another device."}}, 200 
        user = User.query.filter(or_(User.phone==data['phone'],User.device_id=='missing')).first()
        if  user:
                return  {'status': "error","data": {"code":101,"message": "Error you already login to another device."}}, 200 