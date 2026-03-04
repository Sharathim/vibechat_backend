import json
import uuid
import bcrypt
from datetime import datetime
from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__)

DATA_PATH = 'data/users.json'


def load_users():
    try:
        with open(DATA_PATH, 'r') as f:
            return json.load(f)
    except:
        return []


def save_users(users):
    with open(DATA_PATH, 'w') as f:
        json.dump(users, f, indent=2)


def get_user_by_token(token):
    users = load_users()
    for u in users:
        if u.get('token') == token:
            return u
    return None


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    users = load_users()

    # Check duplicates
    for u in users:
        if u['email'] == data.get('email'):
            return jsonify({'error': 'Email already exists'}), 400
        if u['username'] == data.get('username'):
            return jsonify({'error': 'Username already taken'}), 400

    password_hash = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
    token = str(uuid.uuid4())

    user = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', ''),
        'username': data.get('username', ''),
        'email': data.get('email', ''),
        'password_hash': password_hash,
        'avatar': data.get('avatar', None),
        'token': token,
        'created_at': datetime.utcnow().isoformat(),
        'playlists': [],
        'liked_songs': []
    }

    users.append(user)
    save_users(users)

    safe_user = {k: v for k, v in user.items() if k not in ('password_hash',)}
    return jsonify({'token': token, 'user': safe_user}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    users = load_users()

    for u in users:
        if u['email'] == data.get('email'):
            if bcrypt.checkpw(data['password'].encode(), u['password_hash'].encode()):
                token = str(uuid.uuid4())
                u['token'] = token
                save_users(users)
                safe_user = {k: v for k, v in u.items() if k not in ('password_hash',)}
                return jsonify({'token': token, 'user': safe_user})
            else:
                return jsonify({'error': 'Invalid password'}), 401

    return jsonify({'error': 'User not found'}), 404


@auth_bp.route('/me', methods=['GET'])
def me():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    safe_user = {k: v for k, v in user.items() if k not in ('password_hash', 'token')}
    return jsonify(safe_user)
