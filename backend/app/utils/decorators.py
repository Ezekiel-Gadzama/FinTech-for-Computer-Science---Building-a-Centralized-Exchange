from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import time


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()

        from ..models.user import User
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)
    return decorated

def rate_limit(max_requests: int, window: int):
    """Rate limiting decorator"""
    requests_dict = {}

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            now = time.time()
            client_ip = request.remote_addr

            if client_ip not in requests_dict:
                requests_dict[client_ip] = []

            # Remove old requests
            requests_dict[client_ip] = [
                req_time for req_time in requests_dict[client_ip]
                if now - req_time < window
            ]

            if len(requests_dict[client_ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429

            requests_dict[client_ip].append(now)
            return f(*args, **kwargs)

        return wrapped

    return decorator


def validate_request(schema):
    """Validate request data against schema"""

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            data = request.get_json()
            errors = schema.validate(data)
            if errors:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            return f(*args, **kwargs)

        return wrapped

    return decorator


def kyc_required(f):
    """Require KYC verification"""

    @wraps(f)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()

        from ..models.user import User
        user = User.query.get(user_id)

        if not user or not user.kyc_verified:
            return jsonify({'error': 'KYC verification required'}), 403

        return f(*args, **kwargs)

    return decorated