"""Cold wallet model for secure storage"""
from datetime import datetime
from .. import db
from decimal import Decimal


class ColdWallet(db.Model):
    """Cold wallet for storing funds offline"""
    __tablename__ = 'cold_wallets'

    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(10), nullable=False, index=True)
    
    # Wallet addresses
    public_address = db.Column(db.String(100), unique=True, nullable=False)
    private_key_encrypted = db.Column(db.Text, nullable=False)  # Encrypted with master key
    
    # Balance tracking
    balance = db.Column(db.Numeric(precision=20, scale=8), default=0, nullable=False)
    
    # Configuration
    hot_wallet_threshold = db.Column(db.Numeric(precision=20, scale=8), default=1000)  # Auto-transfer threshold
    min_transfer_amount = db.Column(db.Numeric(precision=20, scale=8), default=100)  # Minimum transfer size
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_locked = db.Column(db.Boolean, default=False)  # Lock for maintenance
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_transfer_at = db.Column(db.DateTime)
    
    # Relationships
    transfers = db.relationship('ColdWalletTransfer', backref='cold_wallet', lazy='dynamic')

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'currency': self.currency,
            'public_address': self.public_address,
            'balance': float(self.balance),
            'hot_wallet_threshold': float(self.hot_wallet_threshold),
            'min_transfer_amount': float(self.min_transfer_amount),
            'is_active': self.is_active,
            'is_locked': self.is_locked,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_transfer_at': self.last_transfer_at.isoformat() if self.last_transfer_at else None
        }
        return data

    def __repr__(self):
        return f'<ColdWallet {self.currency} balance={self.balance}>'


class ColdWalletTransfer(db.Model):
    """Record of transfers between hot and cold wallets"""
    __tablename__ = 'cold_wallet_transfers'

    id = db.Column(db.Integer, primary_key=True)
    cold_wallet_id = db.Column(db.Integer, db.ForeignKey('cold_wallets.id'), nullable=False)
    
    # Transfer details
    transfer_type = db.Column(db.String(20), nullable=False)  # 'to_cold' or 'from_cold'
    currency = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(precision=20, scale=8), nullable=False)
    
    # Blockchain info
    blockchain_tx_hash = db.Column(db.String(100))
    confirmations = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cold_wallet_id': self.cold_wallet_id,
            'transfer_type': self.transfer_type,
            'currency': self.currency,
            'amount': float(self.amount),
            'blockchain_tx_hash': self.blockchain_tx_hash,
            'confirmations': self.confirmations,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def __repr__(self):
        return f'<ColdWalletTransfer {self.transfer_type} {self.amount} {self.currency}>'

