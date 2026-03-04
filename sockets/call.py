from flask_socketio import emit, join_room
import json


def get_user_by_token(token):
    try:
        with open('data/users.json') as f:
            users = json.load(f)
        for u in users:
            if u.get('token') == token:
                return u
    except:
        pass
    return None


def register_call_events(socketio):
    @socketio.on('call_invite')
    def on_call_invite(data):
        token = data.get('token')
        user = get_user_by_token(token)
        if not user:
            return
        emit('call_incoming', {
            'from': user['id'],
            'from_name': user['name'],
            'from_avatar': user.get('avatar'),
            'session_id': data.get('session_id')
        }, room=f"user_{data.get('to')}")

    @socketio.on('call_accept')
    def on_call_accept(data):
        emit('call_accepted', {'session_id': data.get('session_id')},
             room=f"user_{data.get('to')}")

    @socketio.on('call_decline')
    def on_call_decline(data):
        emit('call_declined', {'session_id': data.get('session_id')},
             room=f"user_{data.get('to')}")

    @socketio.on('call_end')
    def on_call_end(data):
        emit('call_ended_signal', {'session_id': data.get('session_id'), 'duration': data.get('duration', 0)},
             room=f"user_{data.get('to')}")

    @socketio.on('webrtc_offer')
    def on_offer(data):
        emit('webrtc_offer', {'offer': data.get('offer'), 'from': data.get('from')},
             room=f"user_{data.get('to')}")

    @socketio.on('webrtc_answer')
    def on_answer(data):
        emit('webrtc_answer', {'answer': data.get('answer'), 'from': data.get('from')},
             room=f"user_{data.get('to')}")

    @socketio.on('webrtc_ice')
    def on_ice(data):
        emit('webrtc_ice', {'candidate': data.get('candidate'), 'from': data.get('from')},
             room=f"user_{data.get('to')}")
