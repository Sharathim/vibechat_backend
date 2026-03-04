import json
import uuid
from datetime import datetime
from flask_socketio import emit, join_room, leave_room

MESSAGES_PATH = 'data/messages.json'
USERS_PATH = 'data/users.json'


def load_messages():
    try:
        with open(MESSAGES_PATH) as f:
            return json.load(f)
    except:
        return []


def save_messages(msgs):
    with open(MESSAGES_PATH, 'w') as f:
        json.dump(msgs, f, indent=2)


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


def register_chat_events(socketio):
    @socketio.on('join_chat')
    def on_join_chat(data):
        room = data.get('room')
        if room:
            join_room(room)

    @socketio.on('leave_chat')
    def on_leave_chat(data):
        room = data.get('room')
        if room:
            leave_room(room)

    @socketio.on('send_message')
    def on_send_message(data):
        token = data.get('token')
        user = get_user_by_token(token)
        if not user:
            return

        msg = {
            'id': str(uuid.uuid4()),
            'from': user['id'],
            'to': data.get('to'),
            'type': data.get('type', 'text'),
            'content': data.get('content', ''),
            'payload': data.get('payload', {}),
            'timestamp': datetime.utcnow().isoformat(),
            'sender': {
                'id': user['id'],
                'name': user['name'],
                'username': user['username'],
                'avatar': user.get('avatar')
            }
        }

        messages = load_messages()
        messages.append(msg)
        save_messages(messages)

        # Build room ID (sorted user IDs for consistency)
        participants = sorted([user['id'], data.get('to', '')])
        room = f"chat_{'_'.join(participants)}"
        emit('receive_message', msg, room=room)

    @socketio.on('typing')
    def on_typing(data):
        token = data.get('token')
        user = get_user_by_token(token)
        if user:
            participants = sorted([user['id'], data.get('to', '')])
            room = f"chat_{'_'.join(participants)}"
            emit('user_typing', {'from': user['id']}, room=room, include_self=False)

    @socketio.on('stop_typing')
    def on_stop_typing(data):
        token = data.get('token')
        user = get_user_by_token(token)
        if user:
            participants = sorted([user['id'], data.get('to', '')])
            room = f"chat_{'_'.join(participants)}"
            emit('user_stop_typing', {'from': user['id']}, room=room, include_self=False)
