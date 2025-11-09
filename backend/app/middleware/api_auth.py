"""API key authentication middleware"""
from functools import wraps
from flask import request, jsonify, g
from .. import db
from ..models.api_key import APIKey, APIKeyUsage
from ..utils.security import hash_api_key, verify_api_key
from ..middleware.rate_limiter import check_api_key_rate_limit
from datetime import datetime
import time


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key and secret from headers
        api_key = request.headers.get('X-API-Key')
        api_secret = request.headers.get('X-API-Secret')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Find API key record
        api_key_hash = hash_api_key(api_key)
        api_key_record = APIKey.query.filter_by(api_key_hash=api_key_hash).first()
        
        if not api_key_record:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Verify API secret if provided
        if api_secret:
            if not verify_api_key(api_secret, api_key_record.api_secret_hash):
                return jsonify({'error': 'Invalid API secret'}), 401
        
        # Check if key is active
        if not api_key_record.is_active:
            return jsonify({'error': 'API key is inactive'}), 403
        
        # Check if key is expired
        if api_key_record.is_expired():
            return jsonify({'error': 'API key has expired'}), 403
        
        # Check IP whitelist
        if api_key_record.ip_whitelist:
            client_ip = request.remote_addr
            allowed_ips = [ip.strip() for ip in api_key_record.ip_whitelist.split(',')]
            if client_ip not in allowed_ips:
                return jsonify({'error': 'IP address not whitelisted'}), 403
        
        # Check rate limits
        allowed, error = check_api_key_rate_limit(api_key_record)
        if not allowed:
            return jsonify(error), 429
        
        # Store API key record in request context
        g.api_key = api_key_record
        g.user_id = api_key_record.user_id
        
        # Record usage
        start_time = time.time()
        response = f(*args, **kwargs)
        response_time = int((time.time() - start_time) * 1000)
        
        # Log usage (async in production)
        try:
            usage = APIKeyUsage(
                api_key_id=api_key_record.id,
                endpoint=request.path,
                method=request.method,
                ip_address=request.remote_addr,
                status_code=response[1] if isinstance(response, tuple) else 200,
                response_time_ms=response_time
            )
            db.session.add(usage)
            api_key_record.last_used_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error logging API usage: {e}")
        
        return response
    
    return decorated_function


def require_api_permission(permission: str):
    """Decorator to require specific API permission"""
    def decorator(f):
        @wraps(f)
        @require_api_key
        def decorated_function(*args, **kwargs):
            api_key = g.api_key
            
            if permission == 'read' and not api_key.can_read:
                return jsonify({'error': 'Read permission required'}), 403
            if permission == 'trade' and not api_key.can_trade:
                return jsonify({'error': 'Trade permission required'}), 403
            if permission == 'withdraw' and not api_key.can_withdraw:
                return jsonify({'error': 'Withdraw permission required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

