from datetime import datetime
import bcrypt
from eth_account import Account

from .. import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # KYC
    kyc_verified = db.Column(db.Boolean, default=False)
    kyc_level = db.Column(db.Integer, default=0)  # 0: unverified, 1: basic, 2: advanced
    full_name = db.Column(db.String(120))
    country = db.Column(db.String(80))
    phone = db.Column(db.String(20))

    # Wallet
    public_address = db.Column(db.String(42), unique=True, nullable=False)
    private_key_encrypted = db.Column(db.Text, nullable=False)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    wallets = db.relationship('Wallet', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.set_password(password)
        self.create_wallet()

    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def create_wallet(self):
        """Create Ethereum wallet for the user"""
        account = Account.create()
        self.public_address = account.address
        # In production, encrypt this properly
        self.private_key_encrypted = account.key.hex()

    def to_dict(self, include_sensitive=False):
        """Convert user object to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'kyc_verified': self.kyc_verified,
            'kyc_level': self.kyc_level,
            'public_address': self.public_address,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

        if include_sensitive:
            data['full_name'] = self.full_name
            data['country'] = self.country
            data['phone'] = self.phone

        return data

    def __repr__(self):
        return f'<User {self.username}>'
