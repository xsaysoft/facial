#importing Flask
from flask import Flask, jsonify,abort,make_response
from flask import request,Response
import http.client, urllib.request, urllib.parse, urllib.error, base64
from urllib.parse import urlencode, quote_plus
import requests
import secrets,datetime
import jwt,json
from flask_httpauth import HTTPBasicAuth , HTTPTokenAuth # API 
from flask_sqlalchemy import SQLAlchemy # import SQLAlchemy
from sqlalchemy import desc,and_
from flask_marshmallow import Marshmallow # Flask + marshmallow for beautiful APIs to convert SQLAlchemy to jason
from functools import wraps
from database import User,Token,Enroll,Upload
from flask_cors import CORS, cross_origin
#Liviness Detection
from random import randint
from imutils import paths
from skimage.feature import greycomatrix,greycoprops
from skimage.measure import label,regionprops
from sklearn.model_selection import train_test_split
import numpy as np
import cv2,time,os
import pandas as pd
################################################
auth = HTTPBasicAuth()
authToken = HTTPTokenAuth(scheme='Token')


#start App
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///face.db'

db = SQLAlchemy(app) # Creating database Object form SQLAlchemy

CORS(app)
app.config['SECRET_KEY'] ='0307beb835b20ea53845e3230a7d8d6907dcc5957546580e044c846065da0bd7'
ma = Marshmallow(app) # Creating database Object form Marshmallow




# Create A SCHEMA for User Marshmallow
class UserSchema(ma.ModelSchema):
    class Meta:
        model = User 

# Create A SCHEMA for Token Marshmallow
class TokenSchema(ma.ModelSchema):
    class Meta:
        model = Upload

# Create A SCHEMA for Token Marshmallow
class EnrollSchema(ma.ModelSchema):
    class Meta:
        model = Enroll

#SECURE ROUTE USING BASIC AUTH
@auth.get_password
def get_pw(username):
   user = User.query.filter_by(username=username).first()
   if user is not None:
       return user.password
   else:
       return None




#PROTECTED ROUTE WITH TOKEN CALL
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token=None
        if 'aws-token' in request.headers:
            token =request.headers['aws-token']
        
        if not  token:
            return jsonify({'msg': 'Token is missing'}), 401
        try:
            data=jwt.decode(token,app.config['SECRET_KEY'] )
            current_data=data # pass the decode that within the token 
        except:
            return jsonify({'msg': 'Invalid Token'}), 403

        return f(current_data,*args,**kwargs)
    return decorated


# error to stop alert form using browser
@authToken.error_handler
@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)
#let make a json error call to display nice error call
@authToken.error_handler
@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)
@app.errorhandler(405)
def method_not(error):
    return make_response(jsonify({'error': 'Method Not Allow'}), 405)
@app.errorhandler(500)
def server_error(error):
    return make_response(jsonify({'error': 'Internal Server Error'}), 500)


#*********************FUNCTION CALL******************
#Check & delete  expire token call not in used
def expire_token():
    expiration_time = 10
    limit = datetime.datetime.now() - datetime.timedelta(minutes=expiration_time)
    Token.query.filter(Token.created_time <= limit).delete()
    db.session.commit()




# CREATE PARTION  with SQLAlchemy
@app.route('/app/api/v1.0/partition',methods=['POST'])
def partition():
    if not request.json or not 'partition' in request.json:
        abort(400)
    username=request.json['username']
    password=request.json['password']
    partition=request.json['partition']
    service=request.json['service']
    userData=User(username=username,password=password,partition=partition,service=service)
    db.session.add(userData)
    db.session.commit()
    msg = "Partition Created successfully"
    #return jsonify(msg.json())
    return jsonify({'msg': msg}), 201



#VIEW  PARTITIONS Create
@app.route('/app/api/v1.0/partition/view',methods=['GET'])
def view_partition():
    rows = User.query.all()
    user_schema=UserSchema(many=True)
    result=user_schema.dump(rows).data
    return jsonify({'data': result}), 201



# Generate Token to strat  Biomentric operation  with successful ASW AUTH 
@app.route('/app/api/v1.0/api/token',methods=['GET'])
@auth.login_required # securing the api route
def token_generate():
    #Retrieving Query String Parameters
    partition=request.args['partition'];
    callID=request.args['callID'];
    awsTask=request.args['task']
    results=User.query.filter_by(partition = partition).all()

    if len(results)==0:
        return make_response( jsonify({'msg': 'Invalid Partition '}), 402)
    else:
        for result in results:
            awsUser=result.username
            awsPartition=result.partition
        #encode all  return data to the  token
        token=jwt.encode({'awsPartition': awsPartition,'callID': callID,'awsUser': awsUser, 'awsTask': awsTask,'exp' : datetime.datetime.utcnow()+ datetime.timedelta(minutes=1000)},app.config['SECRET_KEY'])
        # return jsonify({'token': token.decode('UTF-8')}), 201
        return token.decode('UTF-8')
    

 #Token view Using SCHEMA TO DISPLAY SQLALCHEMY
@app.route('/app/api/v1.0/token/view',methods=['GET'])
def view_token():
    rows = Upload.query.all()
    token_schema=TokenSchema(many=True)
    result=token_schema.dump(rows).data
    return jsonify({'data': result}), 201   


#####################################################################################################################################
#                                        SETTING LARGEPERSON GROUP
#
######################################################################################################################################




#setting the server and partition with Azure to perform identification [LargePersonGroup]
#CreateLargePerson
@app.route('/app/api/v1.0/lgp',methods=['PUT'])
@token_required # securing the api route with generated token 
def LargePersonGroup(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/largePersonGroupId"
    partition=request.args['partition'];
    #name=request.args['name'];
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }
   
    payload = "{\r\n    \"name\": \""+current_data['awsUser']+"\",\r\n    \"userData\": \"No User  data attached to partition.\"\r\n}"

    params  = {"largePersonGroupId": partition}
    response = requests.request("PUT",url, data=payload, headers=headers, params=params)
    responseValue=response.text
    if not responseValue:
        return make_response( jsonify({'msg': 'LPG Partition was Created successfully'}), 200)
    else:
        return jsonify(response.json())
    
        
   

#View Created Large Person by Partition

@app.route('/app/api/v1.0/lgp/group',methods=['GET'])
@token_required # securing the api route with generated token 
def get_lpg(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/largePersonGroupId"
    partition=request.args['partition'];
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }

    params  = {"largePersonGroupId": partition}
    
    response = requests.request("GET",url,  headers=headers, params=params)
    return jsonify(response.json())



#GET All Large Person  Partition

@app.route('/app/api/v1.0/lgp/group/all',methods=['GET'])
@token_required # securing the api route with generated token 
def get_lpg_all(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups"
    
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }

    params  = {}
    
    response = requests.request("GET",url,  headers=headers, params=params)
    return jsonify(response.json())



#Delete Large Person Group

@app.route('/app/api/v1.0/lgp/delete',methods=['DELETE'])
@token_required # securing the api route with generated token 
def delete_lpg(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/largePersonGroupId"
    partition=request.args['partition'];
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }

    params  = {"largePersonGroupId": partition}
    
    response = requests.request("DELETE",url,  headers=headers, params=params)
    responseValue=response.text
    if not responseValue:
        return make_response( jsonify({'msg': 'Partition was Deleted successfully'}), 200)
    else:
        return jsonify(response.json())



  #LargePersonGroup - Train : The training task is an asynchronous task.

@app.route('/app/api/v1.0/face/train',methods=['POST'])
@token_required # securing the api route with generated token 
def LargePersonGroupTrain(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/"+current_data['awsPartition']+"/train"
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }
    
    response = requests.request("POST",url, headers=headers)
    responseValue=response.text
    if not responseValue:
        return make_response( jsonify({'msg': 'Partition was  successfully Train'}), 200)
    else:
        return jsonify(response.json())
    
    
#GET train Status

@app.route('/app/api/v1.0/face/train/status',methods=['GET'])
@token_required # securing the api route with generated token 
def get_train_status(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/"+current_data['awsPartition']+"/training"
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }
    
    response = requests.request("GET",url,  headers=headers)
    return jsonify(response.json())



#####################################################################################################################################
#                                        SETTING PERSONS ID IN THE ;LARGE PERSON GROUP STARTING ENRROLLMENT 
#
######################################################################################################################################



#GET All Large PersonGroup person Details

@app.route('/app/api/v1.0/person/all',methods=['GET'])
@token_required # securing the api route with generated token 
def get_person_all(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/"+current_data['awsPartition']+"/persons"
    
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }

    #params  = {"largePersonGroupId": current_data['partition']}
    
    response = requests.request("GET",url,  headers=headers)
    return jsonify(response.json())




#####################################################################################################################################
#                                        SETTING  LARGEFACE LIST FOR FACE SEARCH
#
######################################################################################################################################




#setting the server and partition with Azure to perform identification [LargePersonGroup]
#CreateLargePerson
@app.route('/app/api/v1.0/fs',methods=['PUT'])
@token_required # securing the api route with generated token 
def LargeFaceList(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largefacelists/largeFaceListId"
    partition=request.args['partition'];
    #name=request.args['name'];
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }
   
    payload = "{\r\n    \"name\": \""+current_data['awsUser']+"\",\r\n    \"userData\": \"No User  data attached to partition.\"\r\n}"

    params  = {"largeFaceListId": partition}
    response = requests.request("PUT",url, data=payload, headers=headers, params=params)
    responseValue=response.text
    if not responseValue:
        return make_response( jsonify({'msg': 'Face List Partition was Created successfully'}), 200)
    else:
        return jsonify(response.json())
    



@app.route('/app/api/v1.0/fs/all',methods=['GET'])
@token_required # securing the api route with generated token 
def get_fs_all(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largefacelists"
    
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }

    params  = {}
    
    response = requests.request("GET",url,  headers=headers, params=params)
    return jsonify(response.json())


#####################################################################################################################################
#                                        START BIOMETRIC CALLS
#
######################################################################################################################################
#-----------------------------------------BIOMETRIC CALLS-----------------------------------------
# A route to return all of the available entries in our catalog.
# this route to the api get funtion using the get method/ only for the GET HTTP method.


#Upload person to prepare for BioMetric

@app.route('/app/api/v1.0/upload', methods=['POST']) 
@token_required # securing the api route with generated token
def get_upload(current_data):
    if not request.json or not 'index' in request.json:
        abort(400)
    dataUrl=request.json['DataUrl']
    index=request.json['index']
    
    with open("upload/"+current_data['awsPartition']+ current_data['callID'] +index+".png", "wb") as fh:
        fh.write(base64.decodebytes(dataUrl.encode()))
    
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    image_url = "http://aws.appmartgroup.com/upload/"+current_data['awsPartition']+ current_data['callID'] +index+".png"
    face_api_url = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/detect'

    #Parameter to pass
    headers = {
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key
    }
    params = {
        'returnFaceId': 'true',
        'returnFaceAttributes': 'blur,exposure,noise'
    }

    data = {'url': image_url}

    response = requests.post(face_api_url, params=params, headers=headers, json=data)
    results=response.json()
    awsfaceId= results[0]
    if not awsfaceId['faceId']:
        return jsonify({ "Accepted": False, "Error":'No Face Found'}),403
    else:
       #return jsonify({'awsPersonId':awsPersonId})
       UploadData=Upload(partition=current_data['awsPartition'],faceId=awsfaceId['faceId'],callID=current_data['callID'],Image=image_url,personId=awsfaceId['faceId'],task=current_data['awsTask'] )
       db.session.add(UploadData)
       db.session.commit()
       msg = "Upload successfully"
       return jsonify({"Accepted": True}), 201
    
    return jsonify({"Accepted": False}), 404



#Upload and replace function 
@app.route('/app/api/v1.0/face/upload', methods=['POST']) 
@token_required # securing the api route with generated token
def get_upload_face(current_data):
    if not request.json or not 'index' in request.json:
        abort(400)
    dataUrl=request.json['DataUrl']
    index=request.json['index']
    
    with open("upload/"+current_data['awsPartition']+ current_data['callID'] +index+".png", "wb") as fh:
        fh.write(base64.decodebytes(dataUrl.encode()))
    
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    image_url = "http://aws.appmartgroup.com/upload/"+current_data['awsPartition']+ current_data['callID'] +index+".png"
    face_api_url = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/detect'

    #Parameter to pass
    headers = {
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key
    }
    params = {
        'returnFaceId': 'true',
        'returnFaceAttributes': 'blur,exposure,noise'
    }
    
    data = {'url': image_url}
    
    response = requests.post(face_api_url, params=params, headers=headers, json=data)
    results=response.json()
    awsfaceId= results[0]
    if not awsfaceId['faceId']:
        return jsonify({ "Accepted": False, "Error":'No Face Found'}),403
    else:
        UploadData=Upload(partition=current_data['awsPartition'],faceId=awsfaceId['faceId'],callID=current_data['callID'],Image=image_url,personId=awsfaceId['faceId'],task=current_data['awsTask'] )
        db.session.add(UploadData)
        db.session.commit()
        return jsonify({"Accepted": True}), 201

    return jsonify({"Accepted": False}), 404


#Delete

@app.route('/app/api/v1.0/delete',methods=['Delete'])
@token_required # securing the api route with generated token 
def Upload_delete(current_data):
    user= Upload.query.filter_by(id=411860).delete()
    db.session.commit()
    if not user:
        return  jsonify({'status': "error","data": {"code":102, "message":'ClassID does not exist' }}), 200
    else:
        return  jsonify({'status': "success","data": {"code":100,"message":'ClassID data has been deleted'}}), 200

@app.route('/app/api/v1.0/en_delete',methods=['Delete'])
@token_required # securing the api route with generated token 
def Enroll_delete(current_data):
    user= Enroll.query.filter_by(callID=current_data['callID'],partition=current_data['awsPartition']).delete()
    if not user:
        return  jsonify({'status': "error","data": {"code":102, "message":'ClassID does not exist' }}), 200
    else:

        db.session.commit()
        return  jsonify({'status': "success","data": {"code":100,"message":'ClassID data has been deleted'}}), 200
#GET

@app.route('/app/api/v1.0/upload_get',methods=['Get'])
@token_required # securing the api route with generated token 
def Upload_get(current_data):
    faceIds=Upload.query.filter_by(callID = current_data['callID'],partition=current_data['awsPartition']).order_by(desc(Upload.id)).all()
    token_schema=TokenSchema(many=True)
    result=token_schema.dump(faceIds).data
    return  jsonify({'status': "success","data": {"code":100,"message":result}}), 200

@app.route('/app/api/v1.0/enroll_get',methods=['Get'])
@token_required # securing the api route with generated token 
def Enroll_get(current_data):
    faceIds=Enroll.query.filter_by(callID = current_data['callID'],partition=current_data['awsPartition']).order_by(desc(Enroll.id)).limit(1).all()
    token_schema=EnrollSchema(many=True)
    result=token_schema.dump(faceIds).data
    return  jsonify({'status': "success","data": {"code":100,"message":result}}), 200

#####################################################################################################################################
#                                        LARGEPERSON GROUP ENROLLMENT 
#
######################################################################################################################################


@app.route('/app/api/v1.0/enroll',methods=['POST'])
@token_required # securing the api route with generated token 
def Person_create(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/largePersonGroupId/persons"
    
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }
    payload = "{\r\n    \"name\": \"Aws\",\r\n    \"userData\": \"No data attached .\"\r\n}"
    params  = {"largePersonGroupId": current_data['awsPartition']}
    
    response = requests.request("POST",url, data=payload, headers=headers, params=params)
    results=response.json()

    awsPersonId= results['personId']
    if not awsPersonId:
        return jsonify({'msg': results})
    else:
       #return jsonify({'awsPersonId':awsPersonId})
       ImgUrls=Upload.query.filter_by(callID = current_data['callID'],partition=current_data['awsPartition']).order_by(desc(Upload.id)).limit(1).all()
       if len(ImgUrls)==0:
          return make_response( jsonify({'msg': 'Invalid Token : can not perform Enrollment '}), 403)
       else:
           for ImgUrl in ImgUrls:
                 
                #ADDING FACE TO A PERSON GROUP CREATED
                AddFaceUrl = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/"+current_data['awsPartition']+"/persons/"+awsPersonId+"/persistedfaces?detectionModel=detection_01"
                image_url=ImgUrl.Image
                data = {'url': image_url}
                FaceResponse = requests.request("POST",AddFaceUrl,  headers=headers,  json=data)
                Awsresults=FaceResponse.json()
                awspersistedFaceId= Awsresults['persistedFaceId']
        
                EnrollData=Enroll(partition=current_data['awsPartition'],personId=awsPersonId,callID=current_data['callID'],persistedFaceId=awspersistedFaceId,task=current_data['awsTask'])
                db.session.add(EnrollData)
                db.session.commit()
                msg = "Enrollment successfully"
        
                #Return Enroment successfully but keep processing Training 

                #Train Pratition for Identify 
                TrainUrl = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/"+current_data['awsPartition']+"/train"
                responseTrain = requests.request("POST",TrainUrl, headers=headers)
                responseValue=responseTrain.text
                if not responseValue:
                     return jsonify({'msg': msg}), 201
                else:
                     return jsonify({'error': responseValue})
           #On successful personid is generated...this personId will be use to add a face which perform enrollment
    

#####################################################################################################################################
#                                        LARGEPERSON GROUP IDENTIFICATION
#
######################################################################################################################################



@app.route('/app/api/v1.0/identy', methods=['POST']) 
@token_required # securing the api route with generated token
def get_identify(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"


    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/identify"

    #Parameter to pass
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}
    results = []
    faceIds=Upload.query.filter_by(callID = current_data['callID'],partition=current_data['awsPartition']).order_by(desc(Upload.id)).limit(1).all()
    if len(faceIds)==0:
        return make_response( jsonify({'msg': 'Invalid Token : can not perform identification '}), 403)
    else:
       for faceId in faceIds:
            payload = "{\r\n    \"largePersonGroupId\": \""+ current_data['awsPartition']+"\",\r\n    \"faceIds\": [\r\n        \""+faceId.faceId+"\"\r\n    ],\r\n    \"maxNumOfCandidatesReturned\": 20,\r\n  \"confidenceThreshold\": \"0.1\"\r\n}"
            #payload = "{\r\n    \"largePersonGroupId\": \"sample_group\",\r\n    \"faceIds\": [\r\n        \"c5c24a82-6845-4031-9d5d-978df9175426\"\r\n    ],\r\n    \"maxNumOfCandidatesReturned\": 1,\r\n    \"confidenceThreshold\": 0.5\r\n}"
            response = requests.request("POST",url, data=payload, headers=headers)
            #Return All Matching Record 
            # return jsonify(response.json())
            faces=response.json()
            #Return All Matching Record 
            for face in faces:
                for x in range(len(face['candidates'])):
                    score=face['candidates'][x]['confidence']
                    personId=face['candidates'][x]['personId']
               
                    Awsface=Enroll.query.filter_by(personId=personId,partition=current_data['awsPartition']).limit(1).all()
                    for faceA in Awsface:
                        Matches = {
                        'score' : score,
                        'classID' : faceA.callID,
                        'storage' : 'aws',
                        'personId' : faceA.personId
                    
                         }
                    results.append(Matches)
            return jsonify({'Matches' :results})


#####################################################################################################################################
#                                        LARGEPERSON GROUP VERIFICATION
#
######################################################################################################################################



@app.route('/app/api/v1.0/verify', methods=['POST']) 
@token_required # securing the api route with generated token
def get_verify(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"


    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/verify"

    #Parameter to pass
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}
    faceIds=Upload.query.filter_by(callID = current_data['callID'],partition=current_data['awsPartition']).order_by(desc(Upload.id)).limit(1).all()
    if len(faceIds)==0:
        return make_response( jsonify({'msg': 'Invalid Token : can not perform Verification '}), 403)
    else:
       for faceId in faceIds:
           
            Awsface=Enroll.query.filter_by(callID = current_data['callID'],partition=current_data['awsPartition']).order_by(desc(Enroll.id)).limit(1).all()
            if len(Awsface)==0:
               return make_response( jsonify({'msg': 'Invalid call: PersonId Not Found '}), 404)
            else:
                for faceA in Awsface:
                    
                    payload = "{\r\n    \"faceId\": \""+faceId.faceId+"\",\r\n    \r\n    \"personId\": \""+faceA.personId+"\",\r\n   \"largePersonGroupId\": \""+ current_data['awsPartition']+"\",\r\n    }"
                    #payload = "{\r\n    \"faceId1\": \""+faceA.personId+"\",\r\n    \r\n    \"faceId2\": \""+faceId.faceId+"\",\r\n   }"
                    response = requests.request("POST",url, data=payload, headers=headers)
                    #Return All Matching Record 
                    faces=response.json() 
                    return jsonify({'Enrollid' :faceA.personId,'facid':faceId.faceId,'Matches':faces, 'all':faceId.Image})
               
                


#####################################################################################################################################
#                                        FACE SIMILARTITY  
#
######################################################################################################################################          

#####################################################################################################################################
#                                        FACE SIMILARTITY ENROLLMENT  
#
######################################################################################################################################

@app.route('/app/api/v1.0/face/enroll',methods=['POST'])
@token_required # securing the api route with generated token 
def Face_create(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }
    #return jsonify({'awsPersonId':awsPersonId})
    ImgUrls=Upload.query.filter_by(callID = current_data['callID'],partition=current_data['awsPartition']).order_by(desc(Upload.id)).limit(1).all()
    for ImgUrl in ImgUrls:
             
        #ADDING FACE TO A PERSON GROUP CREATED
        AddFaceUrl = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largefacelists/"+current_data['awsPartition']+"/persistedfaces"
        image_url=ImgUrl.Image
        data = {'url': image_url}
        FaceResponse = requests.request("POST",AddFaceUrl,  headers=headers,  json=data)
        Awsresults=FaceResponse.json()
        awspersistedFaceId= Awsresults['persistedFaceId']


        EnrollData=Enroll(partition=current_data['awsPartition'],callID=current_data['callID'],persistedFaceId=awspersistedFaceId,task=current_data['awsTask'])
        db.session.add(EnrollData)
        db.session.commit()
        msg = "Face Enrollment successfully"

        #Return Enroment successfully but keep processing Training 
        

        #Train Pratition for Identify 
        TrainUrl = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largefacelists/"+current_data['awsPartition']+"/train"
        responseTrain = requests.request("POST",TrainUrl, headers=headers)
        responseValue=responseTrain.text
        if not responseValue:
             return jsonify({'msg': msg}), 201
        else:
             return jsonify({'error': responseValue})
       #On successful personid is generated...this personId will be use to add a face which perform enrollment


#####################################################################################################################################
#                                        FACE SIMILARTITY  IDENIFICATION
#
######################################################################################################################################


@app.route('/app/api/v1.0/face/identy', methods=['POST']) 
@token_required # securing the api route with generated token
def face_identify(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"


    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/findsimilars"

    #Parameter to pass
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}
    results = []
    faceIds=Upload.query.filter_by(callID = current_data['callID'],partition=current_data['awsPartition']).order_by(desc(Upload.id)).limit(1).all()
    if len(faceIds)==0:
        return make_response( jsonify({'msg': 'Invalid Token : No sample to  perform identification '}), 403)
    else:
       for faceId in faceIds:
            payload = "{\r\n    \"faceId\": \""+faceId.faceId+"\",\r\n    \"largeFaceListId\": \""+ current_data['awsPartition']+"\",\r\n    \"maxNumOfCandidatesReturned\": 20,\r\n    \"mode\": \"matchFace\"\r\n}"
           
            response = requests.post(url, data=payload, headers=headers)
            faces=response.json()
    #Return All Matching Record 
            for face in faces:
                Awsface=Enroll.query.filter_by(persistedFaceId=face['persistedFaceId']).limit(1).all()
                for faceA in Awsface:
                    Matches = {
                    'score' : face['confidence'],
                    'classID' : faceA.callID,
                    'storage' : 'aws',
                    'persistedFaceId' : faceA.persistedFaceId
                
                     }
                    results.append(Matches)
            return jsonify({'Matches' :results})
            #return jsonify(response.json())
            

            
#####################################################################################################################################
#                                        END  BIOMETRIC CALLS
#
######################################################################################################################################




@app.route("/api/v1/users", methods=["POST"])
@token_required # securing the api route with generated token
def list_users(current_data):
    dataUrl="upload/"
    return jsonify({"Accepted": True , "DataUrl" : dataUrl}), 201



    #Delete APi 
@app.route('/app/api/v1.0/json', methods=['POST'])
@token_required # securing the api route with generated token 
def json_task(current_data):
    dataUrl=request.json['DataUrl']
    index=request.json['index']
    if not index:
        index=1
    

    with open("upload/"+current_data['awsPartition']+ current_data['callID'] +index+".png", "wb") as fh:
        fh.write(base64.decodebytes(dataUrl.encode()))
    return jsonify({"Accepted": True, "Warnings": [ "ImageTooSmall", "ImageTooBlurry" ]}), 201
    
#Start coding
@app.route('/')
@auth.login_required # securing the api route
def index():
  return auth.username() + ", You want to change your password"  
#   response  = requests.get('https://restcountries.eu/rest/v2/name/united')
#   return jsonify(response.json())

@app.route('/userLogin')
def loginUser():
    aut= request.authorization    
    if not aut:
        return make_response("Auth not verify",401)
    user = User.query.filter_by(username=aut.username).first()
    psd = User.query.filter_by(password=aut.password).first()
   
    if not user or not psd:
        return make_response("incorrect login details",401)
    else:
        return aut.username + ", You want to change your password" 

@app.route('/app/api/v1.0/uploadAWS', methods=['POST']) 
@token_required # securing the api route with generated token
def get_AWSupload(current_data):
    dataUrl=request.json['DataUrl']
    index=request.json['index']
   
    with open("upload/"+current_data['awsPartition']+ current_data['callID'] +index+".png", "wb") as fh:
        fh.write(base64.decodebytes(dataUrl.encode()))
    
    
    return jsonify({"Accepted": True}), 201
    
#####################################################################################################################################
#                                        BIOMETRIC ENROLL FOR FACESREACH DEMO API
#
######################################################################################################################################


@app.route('/app/api/v1.0/demo/upload', methods=['POST']) 
@token_required # securing the api route with generated token
def get_uploadDemo(current_data):
    
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    image_url = "http://aws.appmartgroup.com/upload/199513704389471.png"
    face_api_url = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/detect'

    #Parameter to pass
    headers = {
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key
    }
    params = {
        'returnFaceId': 'true',
        'returnFaceAttributes': 'blur,exposure,noise'
    }

    data = {'url': image_url}

    response = requests.post(face_api_url, params=params, headers=headers, json=data)
    results=response.json()
    awsfaceId= results[0]
    if not awsfaceId['faceId']:
        return jsonify({ "Accepted": False, "Error":'No Face Found'}),403
    else:
       #return jsonify({'awsPersonId':awsPersonId})
       UploadData=Upload(partition=current_data['awsPartition'],faceId=awsfaceId['faceId'],callID=current_data['callID'],Image=image_url,personId=awsfaceId['faceId'],task=current_data['awsTask'] )
       db.session.add(UploadData)
       db.session.commit()
       msg = "Upload successfully"
       return jsonify({"Accepted": True}), 201




#ENROLL
@app.route('/app/api/v1.0/faceT/enroll',methods=['POST'])
@token_required # securing the api route with generated token 
def Person_create_nultrain(current_data):
    subscription_key = "689818b8d4eb48268ec6bb29c04daebb"
    url = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/largePersonGroupId/persons"
    
      #Parameter to pass
    headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
     'cache-control': "no-cache"
    }
    payload = "{\r\n    \"name\": \"Aws\",\r\n    \"userData\": \"No data attached .\"\r\n}"
    params  = {"largePersonGroupId": current_data['awsPartition']}
    
    response = requests.request("POST",url, data=payload, headers=headers, params=params)
    results=response.json()

    awsPersonId= results['personId']
    if not awsPersonId:
        return jsonify({'msg': results})
    else:
       #return jsonify({'awsPersonId':awsPersonId})
       ImgUrls=Upload.query.filter_by(callID = current_data['callID'],partition=current_data['awsPartition']).order_by(desc(Upload.id)).limit(1).all()
       for ImgUrl in ImgUrls:
             
            #ADDING FACE TO A PERSON GROUP CREATED
            AddFaceUrl = "https://westeurope.api.cognitive.microsoft.com/face/v1.0/largepersongroups/"+current_data['awsPartition']+"/persons/"+awsPersonId+"/persistedfaces"
            image_url=ImgUrl.Image
            data = {'url': image_url}
            FaceResponse = requests.request("POST",AddFaceUrl,  headers=headers,  json=data)
            Awsresults=FaceResponse.json()
            awspersistedFaceId= Awsresults['persistedFaceId']

    
            EnrollData=Enroll(partition=current_data['awsPartition'],personId=awsPersonId,callID=current_data['callID'],persistedFaceId=awspersistedFaceId,task=current_data['awsTask'])
            db.session.add(EnrollData)
            db.session.commit()
            msg = "Enrollment successfully"
            return jsonify({'msg': msg}), 201
            #Return Enroment successfully but keep processing Training 
            
    

#####################################################################################################################################
#                                        LIVINESS DECTION
#
######################################################################################################################################

# Perform Images ANALYING 
@app.route('/app/api/v1.0/face/liveness', methods=['POST']) 
@token_required # securing the api route with generated token
def get_Liveness(current_data):
    
#Start Liveness extraction and detection
    haarfile = "haarcascade_frontalface_alt.xml"
    facedetectfile = cv2.CascadeClassifier(haarfile)
    final = []
    index=1
    path = "upload/"+str(current_data['awsPartition'])+ str(current_data['callID']) +str(index)+".png"
    #path = 'upload/19950112656553181.png'
    if (path):  # WHEN WEBCAM IS OPENED
       
        frame = cv2.imread(path)
        image_grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)#CONVERT IMAGE TO GRAY SCALE
        faces = facedetectfile.detectMultiScale(image_grey)

        for x, y, w, h in faces:
            sub_img = frame[y - 10:y + h + 10, x - 10:x + w + 10]
            os.chdir("Face_Extracted")
            cv2.imwrite(str(current_data['awsPartition'])+ str(current_data['callID']) +str(index)+ ".png", sub_img) # SAVE AND RENAME THE FACE REGION

            # EXTRACTING THE FEATURES NOW FROM THE CROPPED IMAGE OF ONLY FRONTAL FACE         
            #print(int(faces[40, 40]))
            #Calculate the luminance with the face pixels

            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            #cv2.imshow("Frame", frame)
            #sub_img = cv2.resize(sub_img,256,256)
    ##########################################################################
            r = sub_img[110, 90, 0]
            g = sub_img[110, 70, 1]
            b = sub_img[110, 90, 2]
            # LUMINANCE FACTOR
            luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b)
            
            #############################################################
            #Cassifer
            histogram = [0] * 3
            for j in range(3):
                histr = cv2.calcHist([frame], [j], None, [256], [0, 256])
                histr *= 255.0 / histr.max()
                histogram[j] = histr
                #print('histogram :')
            ycrcb_hist= np.array(histogram)
            img_ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            

           

            ### MEAN RGB VALUE FOR LIVENESS DETECTION
            a = np.asarray(sub_img)
            image__mean = np.mean(sub_img, axis=0)
            

            ## SKEWNESS - STANDARD DEVIATION,TOTAL DATA_POINTS,MEAN OF DATA
            y_bar = np.mean(sub_img, axis=0)
            #print()
            variance = np.var(a)
            sd = np.std(a)
            sdp_mean=np.std(image__mean)
            img_ycrcb_std= np.std(img_ycrcb)

            gray_image = cv2.cvtColor(sub_img, cv2.COLOR_BGR2GRAY)
            data_points = cv2.countNonZero(gray_image)
            lumm=int(round(luminance))
            #IMAGE BLUR calculating image bluriness
            fm = cv2.Laplacian(image_grey, cv2.CV_64F).var()
            #print("Blurry No: "+str(fm))
            ##########
            if (data_points > 35000 and lumm < 250 and variance > 2550 and sdp_mean < img_ycrcb_std and fm > 50
            ):
                #print(lumm)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255, 0), 2)
                sub_img = frame[y - 10:y + h + 10, x - 10:x + w + 10]
                os.chdir("Original_Extracted")
                cv2.imwrite(str(current_data['awsPartition'])+ str(current_data['callID']) +str(index)+ ".png", sub_img)
                
                return jsonify({"Accepted": True }), 201
                
                
            else:
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                sub_img = frame[y - 10:y + h + 10, x - 10:x + w + 10]
                os.chdir("Fake_Extracted")
                cv2.imwrite(str(current_data['awsPartition'])+ str(current_data['callID']) +str(index)+ ".png", sub_img)
                return jsonify({"Accepted": False,"luminance" : lumm,"Data Points": data_points,"fm": fm,"variance": variance}), 200


#####################################################################################################################################
#                                        LIVINESS DECTION MOBILE
#
######################################################################################################################################

# Perform Images ANALYING 
@app.route('/app/api/v1.0/liveness', methods=['POST']) 
@token_required # securing the api route with generated token
def get_Liveness_dectect(current_data):
    
#Start Liveness extraction and detection
    haarfile = "haarcascade_frontalface_alt.xml"
    facedetectfile = cv2.CascadeClassifier(haarfile)
    final = []
    index=1
    path = "upload/"+str(current_data['awsPartition'])+ str(current_data['callID']) +str(index)+".png"
    if (path):  # WHEN WEBCAM IS OPENED
       
        frame = cv2.imread(path)
        image_grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)#CONVERT IMAGE TO GRAY SCALE
        faces = facedetectfile.detectMultiScale(image_grey)

        for x, y, w, h in faces:
            sub_img = frame[y - 10:y + h + 10, x - 10:x + w + 10]
            os.chdir("Face_Extracted")
            cv2.imwrite(str(current_data['awsPartition'])+ str(current_data['callID']) +str(index)+ ".png", sub_img) # SAVE AND RENAME THE FACE REGION

            # EXTRACTING THE FEATURES NOW FROM THE CROPPED IMAGE OF ONLY FRONTAL FACE         
            #print(int(faces[40, 40]))
            #Calculate the luminance with the face pixels

            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
            #cv2.imshow("Frame", frame)
            #sub_img = cv2.resize(sub_img,256,256)
    ##########################################################################
            r = sub_img[110, 90, 0]
            g = sub_img[110, 70, 1]
            b = sub_img[110, 90, 2]
            # LUMINANCE FACTOR
            luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b)
            
            #############################################################
            #Cassifer
            histogram = [0] * 3
            for j in range(3):
                histr = cv2.calcHist([frame], [j], None, [256], [0, 256])
                histr *= 255.0 / histr.max()
                histogram[j] = histr
                #print('histogram :')
            ycrcb_hist= np.array(histogram)
            img_ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


            ### MEAN RGB VALUE FOR LIVENESS DETECTION
            a = np.asarray(sub_img)
            image__mean = np.mean(sub_img, axis=0)
            
            ## SKEWNESS - STANDARD DEVIATION,TOTAL DATA_POINTS,MEAN OF DATA
            y_bar = np.mean(sub_img, axis=0)
            #print()
            variance = np.var(a)
            sd = np.std(a)
            sdp_mean=np.std(image__mean)
            img_ycrcb_std= np.std(img_ycrcb)

            gray_image = cv2.cvtColor(sub_img, cv2.COLOR_BGR2GRAY)
            data_points = cv2.countNonZero(gray_image)
            lumm=int(round(luminance))
            #IMAGE BLUR calculating image bluriness
            fm = cv2.Laplacian(image_grey, cv2.CV_64F).var()
            #print("Blurry No: "+str(fm))
            ##########
            if (data_points > 35000 and lumm < 250 and variance > 2020 and sdp_mean < img_ycrcb_std and fm > 10
            ):
                #print(lumm)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255, 0), 2)
                sub_img = frame[y - 10:y + h + 10, x - 10:x + w + 10]
                os.chdir("Original_Extracted")
                cv2.imwrite(str(current_data['awsPartition'])+ str(current_data['callID']) +str(index)+ ".png", sub_img)
                
                return jsonify({"Accepted": True }), 201
                
                
            else:
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                sub_img = frame[y - 10:y + h + 10, x - 10:x + w + 10]
                os.chdir("Fake_Extracted")
                cv2.imwrite(str(current_data['awsPartition'])+ str(current_data['callID']) +str(index)+ ".png", sub_img)
                return jsonify({"Accepted": False,"luminance" : lumm,"Data Points": data_points,"fm": fm,"variance": variance,"sdp_mean": sdp_mean,"img_ycrcb_std":img_ycrcb_std }), 200
          

#####################################################################################################################################
#                                        END BIOMETRIC ALL OPERATION 
#
######################################################################################################################################

#####################################################################################################################################
#                                        OTHER API CALLS FROM  MICROSOFT
#
######################################################################################################################################

   

#CreateLargePerson
@app.route('/app/api/v1.0/news',methods=['GET'])
#@token_required # securing the api route with generated token 
def BingNews():
    if not request.args or not 'q' in request.args:
        abort(400)
    searchItem=request.args['q']
    subscription_key = "c5831a096cf2435c9fc4384e5af012c4"
    search_url = "https://api.cognitive.microsoft.com/bing/v7.0/news/search"
    search_term = searchItem
    #name=request.args['name'];
      #Parameter to pass
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
   

    params = {"q": search_term}
    #response = requests.get(search_url, headers=headers, params=params)
    response = requests.request("GET",search_url, headers=headers, params=params)
    responseValue=response.text
    if not responseValue:
        return make_response( jsonify({'msg': 'Generate successfully'}), 200)
    else:
        return jsonify(response.json())

    # response = requests.request("PUT",url, data=payload, headers=headers, params=params)
    # responseValue=response.text
    # if not responseValue:
    #     return make_response( jsonify({'msg': 'Partition was Created successfully'}), 200)
    # else:
    #     return jsonify(response.json())
    
#Trending
@app.route('/app/api/v1.0/news/category',methods=['GET'])
#@token_required # securing the api route with generated token 
def BingTrendNews():
    if not request.args or not 'q' in request.args:
        abort(400)
    searchItem=request.args['q']
    subscription_key = "c5831a096cf2435c9fc4384e5af012c4"
    search_url = "https://api.cognitive.microsoft.com/bing/v7.0/news"
    search_term = searchItem
    #name=request.args['name'];
      #Parameter to pass
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
   

    params = {"Category": search_term}
    #response = requests.get(search_url, headers=headers, params=params)
    response = requests.request("GET",search_url, headers=headers, params=params)
    responseValue=response.text
    if not responseValue:
        return make_response( jsonify({'msg': 'Generate successfully'}), 200)
    else:
        return jsonify(response.json())
# This set dbug mode to enable reload new changes add to your app
if __name__=='__main__':
    app.run()

