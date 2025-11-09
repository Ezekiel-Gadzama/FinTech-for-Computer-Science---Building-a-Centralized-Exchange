"""Rate limiting middleware using Redis"""
from functools import wraps
from flask import request, jsonify, g
from .. import redis_client
import time


def get_redis_client():
    """Get Redis client"""
    from .. import redis_client
    return redis_client


def rate_limit_by_api_key(max_requests: int, window: int, key_func=None):
    """Rate limit decorator for API key authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from request
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            # Get rate limit key
            if key_func:
                rate_limit_key = key_func(api_key)
            else:
                rate_limit_key = f"rate_limit:api_key:{api_key}"
            
            redis = get_redis_client()
            if not redis:
                # If Redis is not available, allow request (fallback)
                return f(*args, **kwargs)
            
            # Check rate limit
            current = redis.get(rate_limit_key)
            if current and int(current) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': max_requests,
                    'window': window
                }), 429
            
            # Increment counter
            pipe = redis.pipeline()
            pipe.incr(rate_limit_key)
            pipe.expire(rate_limit_key, window)
            pipe.execute()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def rate_limit_by_ip(max_requests: int, window: int):
    """Rate limit decorator based on IP address"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = request.remote_addr
            rate_limit_key = f"rate_limit:ip:{ip_address}"
            
            redis = get_redis_client()
            if not redis:
                return f(*args, **kwargs)
            
            current = redis.get(rate_limit_key)
            if current and int(current) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': max_requests,
                    'window': window
                }), 429
            
            pipe = redis.pipeline()
            pipe.incr(rate_limit_key)
            pipe.expire(rate_limit_key, window)
            pipe.execute()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_api_key_rate_limit(api_key_record):
    """Check if API key has exceeded rate limits"""
    redis = get_redis_client()
    if not redis:
        return True, None
    
    now = time.time()
    
    # Check per-minute limit
    minute_key = f"api_key:{api_key_record.id}:minute"
    minute_count = redis.get(minute_key)
    if minute_count and int(minute_count) >= api_key_record.rate_limit_per_minute:
        return False, {'error': 'Rate limit exceeded (per minute)', 'limit': api_key_record.rate_limit_per_minute}
    
    # Check per-hour limit
    hour_key = f"api_key:{api_key_record.id}:hour"
    hour_count = redis.get(hour_key)
    if hour_count and int(hour_count) >= api_key_record.rate_limit_per_hour:
        return False, {'error': 'Rate limit exceeded (per hour)', 'limit': api_key_record.rate_limit_per_hour}
    
    # Check per-day limit
    day_key = f"api_key:{api_key_record.id}:day"
    day_count = redis.get(day_key)
    if day_count and int(day_count) >= api_key_record.rate_limit_per_day:
        return False, {'error': 'Rate limit exceeded (per day)', 'limit': api_key_record.rate_limit_per_day}
    
    # Increment counters
    pipe = redis.pipeline()
    pipe.incr(minute_key)
    pipe.expire(minute_key, 60)
    pipe.incr(hour_key)
    pipe.expire(hour_key, 3600)
    pipe.incr(day_key)
    pipe.expire(day_key, 86400)
    pipe.execute()
    
    return True, None

