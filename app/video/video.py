"""Audio Recording Socket.IO Example

Implements server-side audio recording.
"""
from io import StringIO , BytesIO
from flask import Blueprint, render_template, request, session, url_for
from flask_socketio import emit
from app import socketio
from PIL import Image
import imutils
import numpy as np
import argparse
import time
import cv2
import io
import base64
import logging

video_bp = Blueprint('video', __name__, static_folder='static',
               template_folder='templates')
             
facedetectfile = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

@video_bp.route('/')
def index():
    """Return the client application."""
    video_url = url_for('video.index', _external=True)
    return render_template('video/main.html', video_url=video_url)


@socketio.on('image',namespace='/video')
def image(data_image):
    sbuf = StringIO()
    sbuf.write(data_image)
    
    # Take in base64 string and return PIL image
    b = io.BytesIO(base64.b64decode(data_image))
    pimg = Image.open(b)
  
   
    # Process the image frame
    frame= cv2.cvtColor(np.array(pimg), cv2.COLOR_BGR2RGB)
    image_grey= cv2.cvtColor(np.array(pimg), cv2.COLOR_BGR2GRAY) 
    
    faces = facedetectfile.detectMultiScale(image_grey)
    
    if (len(faces) == 0):
        print("faces not found")
        return None
    if (len(faces) > 1):
        print("mutiple faces found")
        return None   
     
    #Crop face from Image from dectect face 
    for x, y, w, h in faces:
            sub_img = frame[y - 40:y + h + 40, x - 40:x + w + 40]
         
    #Draw a line on Dectect Face
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255,0,0), 2)
    #Dectect eyes
    eyes = eye_cascade.detectMultiScale(image_grey)
    for (ex,ey,ew,eh) in eyes:
        cv2.rectangle(frame,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)
   
   
    

    imgencode = cv2.imencode('.jpg', sub_img)[1]

    # base64 encode
    stringData = base64.b64encode(imgencode).decode('utf-8')
    b64_src = 'data:image/jpg;base64,'
    stringData = b64_src + stringData

    # emit the frame back
    emit('response_back', stringData)
