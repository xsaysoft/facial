#
#@KEVIN Biometric Module  
#
from flask import request
from flask_restful import Resource
from app.auth.util.token import token_required,SECRET_KEY,auth,authToken
from app.auth.service.resource import random_gentarted,save_changes ,verify_expire_code
from app.auth.util.__code import SUCCESSFUL, FAILED
import jwt,json,secrets,datetime
import cv2 

#CONST
face_alg = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

#
#Facial Detection 
#

class FacialDetResource(Resource):
   @token_required
   def post(self):

        json_data = request.get_json(force=True)
        if not json_data:
               return  {'status': "error","data": {"code":107,"message": "No input data provided." }}, 400
        data = json_data
         

        