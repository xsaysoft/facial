import os
from flask import Flask,Blueprint
from flask_restful import reqparse, abort, Api, Resource

from app.auth.controller.Auth import RegResource,ValidateResource,PasswordSetResource,LoginSetResource,SplashSetResource,HomeResource
from app.auth.controller.Facial import FacialDetResource

app_service = Blueprint('api', __name__)
api = Api(app_service)


##
## Actually setup the Api resource routing here
##
api.add_resource(HomeResource, '/home')
api.add_resource(RegResource, '/v1/registration')
api.add_resource(ValidateResource, '/v1/validate')
api.add_resource(PasswordSetResource, '/v1/password_set')
api.add_resource(LoginSetResource, '/v1/login')
api.add_resource(SplashSetResource, '/v1/splashscreen')

##
##Facial endpoints
##
api.add_resource(FacialDetResource, '/f1/face_dection')

