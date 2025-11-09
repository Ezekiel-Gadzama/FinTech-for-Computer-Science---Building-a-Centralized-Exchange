from datetime import datetime
from .. import db
import uuid


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    # CHANGED: Remove unique constraint and use Text
    transaction_id = db.Column(db.Text, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Transaction details
    transaction_type = db.Column(db.String(20), nullable=False, index=True)  # deposit, withdraw, trade, fee
    currency = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(precision=20, scale=8), nullable=False)

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled

    # Additional info
    description = db.Column(db.Text)
    reference_id = db.Column(db.String(100))  # External reference (blockchain tx, order id, etc.)

    # Blockchain info (for deposits/withdrawals)
    blockchain_address = db.Column(db.String(100))
    blockchain_tx_hash = db.Column(db.String(100))
    confirmations = db.Column(db.Integer, default=0)

    # Timestamps - CHANGED: Use timezone=True
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime(timezone=True))

    # REMOVED: No __table_args__ with unique constraints

    def complete(self):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()

    def fail(self, reason=None):
        """Mark transaction as failed"""
        self.status = 'failed'
        if reason:
            self.description = f"{self.description or ''}\nFailed: {reason}"

    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'currency': self.currency,
            'amount': float(self.amount),
            'status': self.status,
            'description': self.description,
            'reference_id': self.reference_id,
            'blockchain_address': self.blockchain_address,
            'blockchain_tx_hash': self.blockchain_tx_hash,
            'confirmations': self.confirmations,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def __repr__(self):
        return f'<Transaction {self.transaction_id} {self.transaction_type} {self.amount} {self.currency}>'