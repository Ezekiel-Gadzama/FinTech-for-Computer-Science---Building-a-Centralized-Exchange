"""API Key management routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.api_key import APIKey, APIKeyUsage
from ..utils.security import generate_api_key, hash_api_key
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('api_keys', __name__, url_prefix='/api/api-keys')


@bp.route('', methods=['POST'])
@jwt_required()
def create_api_key():
    """Create a new API key"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        name = data.get('name', 'My API Key')
        can_read = data.get('can_read', True)
        can_trade = data.get('can_trade', False)
        can_withdraw = data.get('can_withdraw', False)
        ip_whitelist = data.get('ip_whitelist', '')
        expires_in_days = data.get('expires_in_days')  # Optional expiration
        
        # Generate API key and secret
        api_key = f"ck_{generate_api_key()}"
        api_secret = f"cs_{generate_api_key()}"
        
        # Hash for storage
        api_key_hash = hash_api_key(api_key)
        api_secret_hash = hash_api_key(api_secret)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create API key record
        api_key_record = APIKey(
            user_id=current_user_id,
            name=name,
            api_key_hash=api_key_hash,
            api_secret_hash=api_secret_hash,
            can_read=can_read,
            can_trade=can_trade,
            can_withdraw=can_withdraw,
            ip_whitelist=ip_whitelist,
            expires_at=expires_at
        )
        
        db.session.add(api_key_record)
        db.session.commit()
        
        # Return keys only once (they won't be stored in plain text)
        return jsonify({
            'message': 'API key created successfully',
            'api_key': {
                'id': api_key_record.key_id,
                'name': api_key_record.name,
                'api_key': api_key,  # Only shown once
                'api_secret': api_secret,  # Only shown once
                'can_read': can_read,
                'can_trade': can_trade,
                'can_withdraw': can_withdraw,
                'expires_at': expires_at.isoformat() if expires_at else None
            },
            'warning': 'Save these credentials securely. They cannot be retrieved later.'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['GET'])
@jwt_required()
def list_api_keys():
    """List user's API keys"""
    try:
        current_user_id = get_jwt_identity()
        
        api_keys = APIKey.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'api_keys': [key.to_dict() for key in api_keys]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<key_id>', methods=['GET'])
@jwt_required()
def get_api_key(key_id):
    """Get specific API key details"""
    try:
        current_user_id = get_jwt_identity()
        
        api_key = APIKey.query.filter_by(
            key_id=key_id,
            user_id=current_user_id
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        return jsonify({'api_key': api_key.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<key_id>', methods=['DELETE'])
@jwt_required()
def delete_api_key(key_id):
    """Delete an API key"""
    try:
        current_user_id = get_jwt_identity()
        
        api_key = APIKey.query.filter_by(
            key_id=key_id,
            user_id=current_user_id
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        db.session.delete(api_key)
        db.session.commit()
        
        return jsonify({'message': 'API key deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<key_id>', methods=['PUT'])
@jwt_required()
def update_api_key(key_id):
    """Update API key permissions"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        api_key = APIKey.query.filter_by(
            key_id=key_id,
            user_id=current_user_id
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Update permissions
        if 'can_read' in data:
            api_key.can_read = data['can_read']
        if 'can_trade' in data:
            api_key.can_trade = data['can_trade']
        if 'can_withdraw' in data:
            api_key.can_withdraw = data['can_withdraw']
        if 'is_active' in data:
            api_key.is_active = data['is_active']
        if 'ip_whitelist' in data:
            api_key.ip_whitelist = data['ip_whitelist']
        if 'name' in data:
            api_key.name = data['name']
        
        db.session.commit()
        
        return jsonify({
            'message': 'API key updated successfully',
            'api_key': api_key.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<key_id>/usage', methods=['GET'])
@jwt_required()
def get_api_key_usage(key_id):
    """Get API key usage statistics"""
    try:
        current_user_id = get_jwt_identity()
        
        api_key = APIKey.query.filter_by(
            key_id=key_id,
            user_id=current_user_id
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Get usage stats
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        usage_last_hour = APIKeyUsage.query.filter(
            APIKeyUsage.api_key_id == api_key.id,
            APIKeyUsage.created_at >= last_hour
        ).count()
        
        usage_last_day = APIKeyUsage.query.filter(
            APIKeyUsage.api_key_id == api_key.id,
            APIKeyUsage.created_at >= last_day
        ).count()
        
        total_usage = APIKeyUsage.query.filter_by(api_key_id=api_key.id).count()
        
        return jsonify({
            'api_key_id': key_id,
            'usage': {
                'last_hour': usage_last_hour,
                'last_day': usage_last_day,
                'total': total_usage
            },
            'rate_limits': {
                'per_minute': api_key.rate_limit_per_minute,
                'per_hour': api_key.rate_limit_per_hour,
                'per_day': api_key.rate_limit_per_day
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

