from flask_socketio import emit, join_room, leave_room
from .. import socketio
from flask_jwt_extended import decode_token
from flask import request

connected_users = {}


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')
    if request.sid in connected_users:
        del connected_users[request.sid]


@socketio.on('authenticate')
def handle_authenticate(data):
    """Authenticate WebSocket connection"""
    try:
        token = data.get('token')
        if token:
            decoded = decode_token(token)
            user_id = decoded['sub']
            connected_users[request.sid] = user_id
            emit('authenticated', {'user_id': user_id})
    except Exception as e:
        emit('auth_error', {'error': str(e)})


@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to trading pair updates"""
    pair = data.get('pair')
    if pair:
        join_room(f'pair_{pair}')
        emit('subscribed', {'pair': pair})


@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Unsubscribe from trading pair updates"""
    pair = data.get('pair')
    if pair:
        leave_room(f'pair_{pair}')
        emit('unsubscribed', {'pair': pair})


@socketio.on('ping')
def handle_ping():
    """Handle ping for connection keep-alive"""
    emit('pong')
