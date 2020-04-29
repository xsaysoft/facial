"""Biometric Socket.IO .
"""

from flask import Blueprint, render_template, request, session, url_for,jsonify,abort,make_response
from flask_socketio import emit
from app.face.utils import base64_to_pil_image ,blur_dection,makDir,random_gentarted
from app.face.api.face_f import train,predict,face_distance_to_conf
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



face_bp = Blueprint('face', __name__, static_folder='static',
               template_folder='templates')
facedetectfile = cv2.CascadeClassifier('haar_model/haarcascade_frontalface_alt.xml')
eye_cascade = cv2.CascadeClassifier('haar_model/haarcascade_eye.xml')          

@face_bp.route('/')
def index():
    """Return the client application."""
    face_url = url_for('face.index', _external=True)
    return render_template('face/main.html', video_url=face_url)

@face_bp.route('/training')
def enrollment():
    """Return the client application."""
    train("face_extracted/train", model_save_path="face_extracted/trained_dir/dataset_faces.dat", n_neighbors=2)
    return jsonify({'data': "Training complete!"}), 201
   

@socketio.on('connect', namespace='/face')
def on_connect():
    """A new user connects to the Biometric."""
    if request.args.get('phone') is None:
        return False
    session['phone'] = request.args['phone']
    emit('message', {'message': session['phone'] + ' has connected.'})


@socketio.on('image',namespace='/face')
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
    if blur > 450:
        print("image too blur")
        msg= {'status': "error","data": {"code":101, "message":"image too blur"}}
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
  
    #Create Image for Identification in face dir
    print("create folder")
    makDir("face_extracted/faces/"+session['phone'])
    with open("face_extracted/faces/"+session['phone']+"/"+session['phone']+".png", "wb") as fh:
         fh.write(base64.decodebytes(dataUrl.encode()))

    # Start Recongnizing face 

    for image_file in os.listdir("face_extracted/faces/"+session['phone']):
        full_file_path = os.path.join("face_extracted/faces/"+session['phone'], image_file)

        print("Looking for faces in {}".format(image_file))

        predictions = predict(full_file_path, model_path="face_extracted/trained_dir/dataset_faces.dat")
        print(predictions)
        # Print results on the console
        for name, (top, right, bottom, left) in predictions:
            print("- Found {} at ({}, {})".format(name, left, top,right,bottom))
            
    if (name!=0):
        msg= {'status': "error","data": {"code":301, "message":"Biometric face found","biomeric_id":name}} 
        emit('response_back',msg)
        return None

    makDir("face_extracted/train/"+session['phone'])
    with open("face_extracted/train/"+session['phone']+"/"+session['phone']+str(random_gentarted(4))+".png", "wb") as fh:
         fh.write(base64.decodebytes(dataUrl.encode()))

    #start training imgages 
    train("face_extracted/train", model_save_path="face_extracted/trained_dir/dataset_faces.dat", n_neighbors=2)
    print("Training complete!")
    
    msg = {'status': "success","data": {"code":100,"message":"Biometric enrolled"}}
    emit('response_back',msg)
    # emit the frame back