"""Chat Socket.IO Example

Implements a simple chat server.
"""
from flask import Blueprint, render_template, request, session, url_for
from flask_socketio import emit
from app import socketio

chat_bp = Blueprint('chat', __name__, static_folder='static',
               template_folder='templates')

 
@chat_bp.route('/')
def index():
    """Return the client application."""
    chat_url = url_for('chat.index', _external=True)
    return render_template('chat/main.html', chat_url=chat_url)


@socketio.on('connect', namespace='/chat')
def on_connect():
    """A new user connects to the chat."""
    if request.args.get('username') is None:
        return False
    session['username'] = request.args['username']
    emit('message', {'message': session['username'] + ' has joined.'},
         broadcast=True)


@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    """A user disconnected from the chat."""
    emit('message', {'message': session['username'] + ' has left.'},
         broadcast=True)


@socketio.on('post-message', namespace='/chat')
def on_post_message(message):
    """A user posted a message to the chat."""
    emit('message', {'user': session['username'],
                     'message': message['message']},
         broadcast=True)
