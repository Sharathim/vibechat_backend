import json
import uuid
import time
from flask_socketio import emit, join_room, leave_room

VIBE_SESSIONS_PATH = 'data/vibe_sessions.json'
USERS_PATH = 'data/users.json'

# In-memory active sessions
active_sessions = {}


def get_user_by_token(token):
    try:
        with open(USERS_PATH) as f:
            users = json.load(f)
        for u in users:
            if u.get('token') == token:
                return u
    except:
        pass
    return None


def register_vibe_events(socketio):
    @socketio.on('vibe_request')
    def on_vibe_request(data):
        token = data.get('token')
        user = get_user_by_token(token)
        if not user:
            return
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            'host': user['id'],
            'guest': data.get('to'),
            'song': data.get('song'),
            'playlist': data.get('playlist'),
            'status': 'pending'
        }
        emit('vibe_incoming', {
            'from': user['id'],
            'from_name': user['name'],
            'from_avatar': user.get('avatar'),
            'song': data.get('song'),
            'session_id': session_id
        }, room=f"user_{data.get('to')}")

    @socketio.on('vibe_accept')
    def on_vibe_accept(data):
        token = data.get('token')
        user = get_user_by_token(token)
        if not user:
            return
        session_id = data.get('session_id')
        session = active_sessions.get(session_id)
        if not session:
            return
        session['status'] = 'active'
        start_timestamp = int(time.time() * 1000)
        session['start_timestamp'] = start_timestamp
        join_room(f"vibe_{session_id}")
        emit('vibe_start', {
            'session_id': session_id,
            'song': session['song'],
            'start_timestamp': start_timestamp,
            'host': session['host'],
            'guest': session['guest']
        }, room=f"vibe_{session_id}")
        # Also emit to host
        emit('vibe_start', {
            'session_id': session_id,
            'song': session['song'],
            'start_timestamp': start_timestamp,
            'host': session['host'],
            'guest': session['guest']
        }, room=f"user_{session['host']}")

    @socketio.on('vibe_decline')
    def on_vibe_decline(data):
        session_id = data.get('session_id')
        session = active_sessions.get(session_id)
        if session:
            emit('vibe_declined', {'session_id': session_id}, room=f"user_{session['host']}")
            del active_sessions[session_id]

    @socketio.on('vibe_join_room')
    def on_vibe_join_room(data):
        join_room(f"vibe_{data.get('session_id')}")

    @socketio.on('vibe_pause')
    def on_vibe_pause(data):
        session_id = data.get('session_id')
        emit('vibe_paused', {'timestamp': data.get('timestamp')}, room=f"vibe_{session_id}", include_self=False)

    @socketio.on('vibe_resume')
    def on_vibe_resume(data):
        session_id = data.get('session_id')
        emit('vibe_resumed', {'timestamp': data.get('timestamp')}, room=f"vibe_{session_id}", include_self=False)

    @socketio.on('vibe_skip')
    def on_vibe_skip(data):
        session_id = data.get('session_id')
        start_timestamp = int(time.time() * 1000)
        emit('vibe_skipped', {
            'next_song': data.get('next_song'),
            'start_timestamp': start_timestamp
        }, room=f"vibe_{session_id}")

    @socketio.on('vibe_end')
    def on_vibe_end(data):
        session_id = data.get('session_id')
        emit('vibe_ended', {}, room=f"vibe_{session_id}")
        if session_id in active_sessions:
            del active_sessions[session_id]

    @socketio.on('vibe_reaction')
    def on_vibe_reaction(data):
        token = data.get('token')
        user = get_user_by_token(token)
        if not user:
            return
        session_id = data.get('session_id')
        emit('vibe_reaction', {
            'emoji': data.get('emoji'),
            'from': user['id']
        }, room=f"vibe_{session_id}")
