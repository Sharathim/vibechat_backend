import json
import bcrypt
from flask import Blueprint, request, jsonify

users_bp = Blueprint('users', __name__)

USERS_PATH = 'data/users.json'


def get_token():
    return request.headers.get('Authorization', '').replace('Bearer ', '')


def load_users():
    try:
        with open(USERS_PATH) as f:
            return json.load(f)
    except:
        return []


def save_users(users):
    with open(USERS_PATH, 'w') as f:
        json.dump(users, f, indent=2)


def get_user_by_token(token):
    users = load_users()
    for u in users:
        if u.get('token') == token:
            return u
    return None


def safe_user(u):
    return {k: v for k, v in u.items() if k not in ('password_hash', 'token')}


@users_bp.route('/search', methods=['GET'])
def search_users():
    token = get_token()
    current = get_user_by_token(token)
    if not current:
        return jsonify({'error': 'Unauthorized'}), 401

    q = request.args.get('q', '').lower()
    users = load_users()
    results = [
        safe_user(u) for u in users
        if u['id'] != current['id'] and (
            q in u['name'].lower() or
            q in u['username'].lower() or
            q in u['email'].lower()
        )
    ]
    return jsonify(results)


@users_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    token = get_token()
    if not get_user_by_token(token):
        return jsonify({'error': 'Unauthorized'}), 401
    users = load_users()
    for u in users:
        if u['id'] == user_id:
            return jsonify(safe_user(u))
    return jsonify({'error': 'Not found'}), 404


@users_bp.route('/me', methods=['PUT'])
def update_me():
    token = get_token()
    user = get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    users = load_users()
    for u in users:
        if u['id'] == user['id']:
            if 'name' in data:
                u['name'] = data['name']
            if 'username' in data:
                u['username'] = data['username']
            if 'avatar' in data:
                u['avatar'] = data['avatar']
            if 'password' in data and data['password']:
                u['password_hash'] = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
            save_users(users)
            return jsonify(safe_user(u))
    return jsonify({'error': 'Not found'}), 404
