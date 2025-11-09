"""API Key model for third-party integrations"""
from datetime import datetime, timedelta
from .. import db
import uuid
import secrets


class APIKey(db.Model):
    """API keys for third-party integrations"""
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Key details
    name = db.Column(db.String(100), nullable=False)  # User-friendly name
    api_key_hash = db.Column(db.String(255), nullable=False)  # Hashed API key
    api_secret_hash = db.Column(db.String(255), nullable=False)  # Hashed API secret
    
    # Permissions
    can_read = db.Column(db.Boolean, default=True)
    can_trade = db.Column(db.Boolean, default=False)
    can_withdraw = db.Column(db.Boolean, default=False)
    
    # IP whitelist
    ip_whitelist = db.Column(db.Text)  # Comma-separated IP addresses
    
    # Rate limits
    rate_limit_per_minute = db.Column(db.Integer, default=60)
    rate_limit_per_hour = db.Column(db.Integer, default=1000)
    rate_limit_per_day = db.Column(db.Integer, default=10000)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    
    def to_dict(self, include_secrets=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'key_id': self.key_id,
            'user_id': self.user_id,
            'name': self.name,
            'can_read': self.can_read,
            'can_trade': self.can_trade,
            'can_withdraw': self.can_withdraw,
            'is_active': self.is_active,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'rate_limit_per_hour': self.rate_limit_per_hour,
            'rate_limit_per_day': self.rate_limit_per_day,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
        
        if include_secrets:
            # Note: Actual secrets are only shown once during creation
            data['ip_whitelist'] = self.ip_whitelist
        
        return data

    def is_expired(self):
        """Check if API key is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    def __repr__(self):
        return f'<APIKey {self.name} user={self.user_id}>'


class APIKeyUsage(db.Model):
    """Track API key usage for rate limiting"""
    __tablename__ = 'api_key_usage'

    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False, index=True)
    
    # Request details
    endpoint = db.Column(db.String(200), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    
    # Response
    status_code = db.Column(db.Integer)
    response_time_ms = db.Column(db.Integer)  # Response time in milliseconds
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'api_key_id': self.api_key_id,
            'endpoint': self.endpoint,
            'method': self.method,
            'ip_address': self.ip_address,
            'status_code': self.status_code,
            'response_time_ms': self.response_time_ms,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<APIKeyUsage key={self.api_key_id} endpoint={self.endpoint}>'

