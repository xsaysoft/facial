from app import create_app ,socketio

from logging.handlers import RotatingFileHandler
import os
if __name__ == "__main__":
    app = create_app("config")
    socketio.run(app, debug=True ,host='127.0.0.1',port=5002)
    #socketio.run(app, debug=True ,host='0.0.0.0',port=5001)
    #uncomment when pushing to docker hub
    #app.run(debug=True,host='0.0.0.0')
    #push to server ,host='192.168.88.37'
    #app.run(debug=True,host='0.0.0.0')
    

 