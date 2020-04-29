from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from datetime import datetime

db = SQLAlchemy()
ma = Marshmallow()
socketio = SocketIO()

def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)
    
    
    
    from app.auth import app_service
    from app.chat import chat_bp
    from app.video import video_bp
    from app.biometric import biometric_bp
    from app.face import face_bp
    app.register_blueprint(app_service, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(video_bp, url_prefix='/video')
    app.register_blueprint(biometric_bp, url_prefix='/biometric')
    app.register_blueprint(face_bp, url_prefix='/face')



    db.init_app(app)
    socketio.init_app(app,cors_allowed_origins="*",engineio_logger=True)

    return app