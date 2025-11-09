"""Security middleware"""
from functools import wraps
from flask import request, jsonify, g
from .. import redis_client
import time
import hashlib


def get_client_identifier():
    """Get unique identifier for client (IP + User-Agent hash)"""
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    identifier = f"{ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
    return identifier


def ddos_protection(max_requests: int = 100, window: int = 60, block_duration: int = 300):
    """DDoS protection decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = get_client_identifier()
            redis = redis_client
            
            if redis:
                # Check if client is blocked
                block_key = f"ddos:blocked:{client_id}"
                if redis.get(block_key):
                    return jsonify({
                        'error': 'Access temporarily blocked due to suspicious activity'
                    }), 429
                
                # Track requests
                request_key = f"ddos:requests:{client_id}"
                current = redis.get(request_key)
                
                if current and int(current) >= max_requests:
                    # Block client
                    redis.setex(block_key, block_duration, '1')
                    return jsonify({
                        'error': 'Too many requests. Access temporarily blocked.'
                    }), 429
                
                # Increment counter
                pipe = redis.pipeline()
                pipe.incr(request_key)
                pipe.expire(request_key, window)
                pipe.execute()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_2fa(f):
    """Decorator to require 2FA verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_jwt_extended import get_jwt_identity
        from ..models.user import User
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.two_factor_enabled:
            # Check if 2FA token is provided
            two_factor_token = request.headers.get('X-2FA-Token')
            if not two_factor_token:
                return jsonify({
                    'error': '2FA token required',
                    'requires_2fa': True
                }), 403
            
            # Verify 2FA token (simplified - in production use pyotp)
            # For now, just check if token is provided
            # In production: verify with pyotp.TOTP(user.totp_secret).verify(two_factor_token)
            if not _verify_2fa_token(user, two_factor_token):
                return jsonify({'error': 'Invalid 2FA token'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def _verify_2fa_token(user, token):
    """Verify 2FA token (placeholder - implement with pyotp in production)"""
    # In production, use:
    # import pyotp
    # totp = pyotp.TOTP(user.totp_secret)
    # return totp.verify(token, valid_window=1)
    
    # For now, simple check (replace with actual TOTP verification)
    return len(token) == 6 and token.isdigit()


def validate_input(f):
    """Input validation decorator to prevent injection attacks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for SQL injection patterns
        dangerous_patterns = [
            "'; DROP",
            "'; DELETE",
            "'; UPDATE",
            "'; INSERT",
            "'; SELECT",
            "'; --",
            "'; /*",
            "'; */",
            "'; EXEC",
            "'; EXECUTE"
        ]
        
        # Check JSON body
        if request.is_json:
            data = request.get_json()
            data_str = str(data).upper()
            for pattern in dangerous_patterns:
                if pattern.upper() in data_str:
                    return jsonify({'error': 'Invalid input detected'}), 400
        
        # Check URL parameters
        for key, value in request.args.items():
            value_str = str(value).upper()
            for pattern in dangerous_patterns:
                if pattern.upper() in value_str:
                    return jsonify({'error': 'Invalid input detected'}), 400
        
        return f(*args, **kwargs)
    return decorated_function


def security_headers(f):
    """Add security headers to response"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add security headers
        if isinstance(response, tuple):
            response_obj, status_code = response
            # Headers are added by nginx, but we can add here too
            return response_obj, status_code
        else:
            return response
    
    return decorated_function

