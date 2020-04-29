"""Biometric Socket.IO .
"""

from flask import Blueprint, render_template, request, session, url_for,jsonify,abort,make_response
from flask_socketio import emit
from app.biometric.utils.utils import base64_to_pil_image ,blur_dection
from app import socketio
from PIL import Image
import imutils
import numpy as np
import argparse
import time
import cv2,time,os
import io
import base64
import logging

biometric_bp = Blueprint('biometric', __name__, static_folder='static',
               template_folder='templates')
             
facedetectfile = cv2.CascadeClassifier('haar_model/haarcascade_frontalface_alt.xml')
eye_cascade = cv2.CascadeClassifier('haar_model/haarcascade_eye.xml')

@biometric_bp.route('/')
def index():
    """Return the client application."""
    video_url = url_for('biometric.index', _external=True)
    return render_template('biometric/main.html', video_url=video_url)


@socketio.on('connect', namespace='/biometric')
def on_connect():
    """A new user connects to the Biometric."""
    if request.args.get('phone') is None:
        return False
    session['phone'] = request.args['phone']
    emit('message', {'message': session['phone'] + ' has connected.'})

@socketio.on('image',namespace='/biometric')
def image(data_image):
    # Take in base64 string and return PIL image
    pimg = base64_to_pil_image(data_image)
  
   
    # Process the image frame
    frame= cv2.cvtColor(np.array(pimg), cv2.COLOR_BGR2RGB)
    image_grey= cv2.cvtColor(np.array(pimg), cv2.COLOR_BGR2GRAY) 
    
    faces = facedetectfile.detectMultiScale(image_grey)
    eyes = eye_cascade.detectMultiScale(image_grey)
    blur= blur_dection(image_grey)
    print('blur')
    print(blur)
    if blur > 150:
        print("image too blur")
        msg= {'status': "error","data": {"code":102, "message":"image too blur"}}
        emit('response_back',msg)
        return None
    if (len(faces) == 0):
        print("faces not found")
        msg= {'status': "error","data": {"code":102, "message":"face not found"}}
        emit('response_back',msg)
        return None
    if (len(faces) > 1):
        print("mutiple faces found")
        msg= {'status': "error","data": {"code":103, "message":"mutiple faces found"}} 
        emit('response_back',msg)
        return None
    if(len(eyes) == 0):
        print("eye not found")
        msg= {'status': "error","data": {"code":104, "message":"eyes not found"}}
        emit('response_back',msg)
        return None
    
    #Crop face from Image from dectect face 
    for x, y, w, h in faces:
            sub_img = frame[y - 40:y + h + 40, x - 40:x + w + 40]

    imgencode = cv2.imencode('.jpg', sub_img)[1]

     # base64 encode
    dataUrl = base64.b64encode(imgencode).decode('utf-8')
    
    with open("face_extracted/"+session['phone']+".png", "wb") as fh:
         fh.write(base64.decodebytes(dataUrl.encode()))


    msg = {'status': "success","data": {"code":100}}
    emit('response_back',msg)
    # emit the frame back
    
