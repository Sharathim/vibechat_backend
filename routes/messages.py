import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

messages_bp = Blueprint('messages', __name__)

MESSAGES_PATH = 'data/messages.json'
USERS_PATH = 'data/users.json'


def get_token():
    return request.headers.get('Authorization', '').replace('Bearer ', '')


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


def load_messages():
    try:
        with open(MESSAGES_PATH) as f:
            return json.load(f)
    except:
        return []


def save_messages(msgs):
    with open(MESSAGES_PATH, 'w') as f:
        json.dump(msgs, f, indent=2)


@messages_bp.route('/<other_user_id>', methods=['GET'])
def get_messages(other_user_id):
    token = get_token()
    user = get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    messages = load_messages()
    conversation = [
        m for m in messages
        if (m['from'] == user['id'] and m['to'] == other_user_id) or
           (m['from'] == other_user_id and m['to'] == user['id'])
    ]
    conversation.sort(key=lambda x: x['timestamp'])
    return jsonify(conversation)


@messages_bp.route('/send', methods=['POST'])
def send_message():
    token = get_token()
    user = get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    messages = load_messages()
    msg = {
        'id': str(uuid.uuid4()),
        'from': user['id'],
        'to': data.get('to'),
        'type': data.get('type', 'text'),
        'content': data.get('content', ''),
        'payload': data.get('payload', {}),
        'timestamp': datetime.utcnow().isoformat()
    }
    messages.append(msg)
    save_messages(messages)
    return jsonify(msg), 201


@messages_bp.route('/conversations', methods=['GET'])
def get_conversations():
    token = get_token()
    user = get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    messages = load_messages()
    try:
        with open(USERS_PATH) as f:
            all_users = json.load(f)
    except:
        all_users = []

    users_map = {u['id']: u for u in all_users}

    # Find all unique conversation partners
    partner_ids = set()
    for m in messages:
        if m['from'] == user['id']:
            partner_ids.add(m['to'])
        elif m['to'] == user['id']:
            partner_ids.add(m['from'])

    conversations = []
    for pid in partner_ids:
        partner = users_map.get(pid)
        if not partner:
            continue
        # Get last message
        conv_msgs = [
            m for m in messages
            if (m['from'] == user['id'] and m['to'] == pid) or
               (m['from'] == pid and m['to'] == user['id'])
        ]
        conv_msgs.sort(key=lambda x: x['timestamp'])
        last_msg = conv_msgs[-1] if conv_msgs else None
        unread = sum(1 for m in conv_msgs if m['to'] == user['id'] and not m.get('read', False))

        conversations.append({
            'user': {
                'id': partner['id'],
                'name': partner['name'],
                'username': partner['username'],
                'avatar': partner.get('avatar')
            },
            'last_message': last_msg,
            'unread': unread
        })

    conversations.sort(key=lambda x: x['last_message']['timestamp'] if x['last_message'] else '', reverse=True)
    return jsonify(conversations)
