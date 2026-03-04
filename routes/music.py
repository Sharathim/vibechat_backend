import os
import json
import uuid
import base64
from flask import Blueprint, request, jsonify, send_file, Response
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen import File as MutagenFile

music_bp = Blueprint('music', __name__)

MUSIC_DIR = 'music'
PLAYLISTS_PATH = 'data/playlists.json'
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


def load_playlists():
    try:
        with open(PLAYLISTS_PATH) as f:
            return json.load(f)
    except:
        return []


def save_playlists(pl):
    with open(PLAYLISTS_PATH, 'w') as f:
        json.dump(pl, f, indent=2)


def get_song_metadata(filename):
    path = os.path.join(MUSIC_DIR, filename)
    meta = {
        'filename': filename,
        'title': os.path.splitext(filename)[0],
        'artist': 'Unknown Artist',
        'album': 'Unknown Album',
        'duration': 0,
        'has_art': False
    }
    try:
        audio = MutagenFile(path)
        if audio:
            tags = audio.tags
            if tags:
                if hasattr(tags, 'get'):
                    title = tags.get('TIT2') or tags.get('title')
                    artist = tags.get('TPE1') or tags.get('artist')
                    album = tags.get('TALB') or tags.get('album')
                    if title:
                        meta['title'] = str(title[0]) if hasattr(title, '__iter__') and not isinstance(title, str) else str(title)
                    if artist:
                        meta['artist'] = str(artist[0]) if hasattr(artist, '__iter__') and not isinstance(artist, str) else str(artist)
                    if album:
                        meta['album'] = str(album[0]) if hasattr(album, '__iter__') and not isinstance(album, str) else str(album)
                # Check for album art
                for key in tags.keys():
                    if key.startswith('APIC'):
                        meta['has_art'] = True
                        break
        if hasattr(audio, 'info') and audio.info:
            meta['duration'] = round(audio.info.length)
    except Exception as e:
        pass
    return meta


@music_bp.route('/songs', methods=['GET'])
def list_songs():
    if not os.path.exists(MUSIC_DIR):
        os.makedirs(MUSIC_DIR)
    songs = []
    for fname in os.listdir(MUSIC_DIR):
        if fname.lower().endswith('.mp3'):
            songs.append(get_song_metadata(fname))
    return jsonify(songs)


@music_bp.route('/stream/<filename>', methods=['GET'])
def stream_song(filename):
    path = os.path.join(MUSIC_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Not found'}), 404
    return send_file(path, mimetype='audio/mpeg', conditional=True)


@music_bp.route('/art/<filename>', methods=['GET'])
def get_art(filename):
    path = os.path.join(MUSIC_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Not found'}), 404
    try:
        audio = MutagenFile(path)
        if audio and audio.tags:
            for key in audio.tags.keys():
                if key.startswith('APIC'):
                    apic = audio.tags[key]
                    return Response(apic.data, mimetype=apic.mime)
    except:
        pass
    return jsonify({'error': 'No art'}), 404


@music_bp.route('/playlists', methods=['GET'])
def get_playlists():
    token = get_token()
    user = get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    playlists = load_playlists()
    user_playlists = [p for p in playlists if p.get('owner_id') == user['id']]
    return jsonify(user_playlists)


@music_bp.route('/playlists', methods=['POST'])
def create_playlist():
    token = get_token()
    user = get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    playlists = load_playlists()
    playlist = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', 'New Playlist'),
        'owner_id': user['id'],
        'owner_name': user['name'],
        'owner_username': user['username'],
        'songs': data.get('songs', []),
        'created_at': __import__('datetime').datetime.utcnow().isoformat()
    }
    playlists.append(playlist)
    save_playlists(playlists)
    return jsonify(playlist), 201


@music_bp.route('/playlists/<playlist_id>', methods=['PUT'])
def update_playlist(playlist_id):
    token = get_token()
    user = get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    playlists = load_playlists()
    for p in playlists:
        if p['id'] == playlist_id and p['owner_id'] == user['id']:
            p.update({k: v for k, v in data.items() if k not in ('id', 'owner_id')})
            save_playlists(playlists)
            return jsonify(p)
    return jsonify({'error': 'Not found'}), 404
