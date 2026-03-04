import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO, join_room
from flask_cors import CORS
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vibechat-secret-key-2024')

ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')

CORS(app, origins=ALLOWED_ORIGINS)
socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS, async_mode='eventlet')

# Register blueprints
from routes.auth import auth_bp
from routes.music import music_bp
from routes.messages import messages_bp
from routes.users import users_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(music_bp, url_prefix='/api/music')
app.register_blueprint(messages_bp, url_prefix='/api/messages')
app.register_blueprint(users_bp, url_prefix='/api/users')

# Register socket events
from sockets.chat import register_chat_events
from sockets.vibe import register_vibe_events
from sockets.call import register_call_events

register_chat_events(socketio)
register_vibe_events(socketio)
register_call_events(socketio)


@socketio.on('register_user')
def on_register_user(data):
    user_id = data.get('user_id')
    if user_id:
        join_room(f"user_{user_id}")


@socketio.on('connect')
def on_connect():
    pass


@socketio.on('disconnect')
def on_disconnect():
    pass


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)