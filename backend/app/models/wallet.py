from datetime import datetime
from .. import db
from decimal import Decimal


class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Currency and balance
    currency = db.Column(db.String(10), nullable=False, index=True)  # BTC, ETH, USDT, etc.
    balance = db.Column(db.Numeric(precision=20, scale=8), default=0, nullable=False)
    locked_balance = db.Column(db.Numeric(precision=20, scale=8), default=0, nullable=False)

    # Wallet type
    wallet_type = db.Column(db.String(10), default='hot')  # hot or cold

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint for user-currency combination
    __table_args__ = (
        db.UniqueConstraint('user_id', 'currency', name='unique_user_currency'),
    )

    @property
    def available_balance(self):
        """Calculate available balance (total - locked)"""
        return self.balance - self.locked_balance

    def lock_balance(self, amount):
        """Lock a certain amount for trading"""
        amount = Decimal(str(amount))
        if amount <= self.available_balance:
            self.locked_balance += amount
            return True
        return False

    def unlock_balance(self, amount):
        """Unlock balance"""
        amount = Decimal(str(amount))
        if amount <= self.locked_balance:
            self.locked_balance -= amount
            return True
        return False

    def add_balance(self, amount):
        """Add to balance"""
        amount = Decimal(str(amount))
        self.balance += amount

    def deduct_balance(self, amount):
        """Deduct from balance"""
        amount = Decimal(str(amount))
        if amount <= self.balance:
            self.balance -= amount
            return True
        return False

    def to_dict(self):
        """Convert wallet to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'currency': self.currency,
            'balance': float(self.balance),
            'locked_balance': float(self.locked_balance),
            'available_balance': float(self.available_balance),
            'wallet_type': self.wallet_type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Wallet user={self.user_id} currency={self.currency} balance={self.balance}>'


class ExchangeWallet(db.Model):
    __tablename__ = 'exchange_wallets'

    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(10), unique=True, nullable=False)
    total_balance = db.Column(db.Numeric(precision=20, scale=8), default=0)
    total_locked = db.Column(db.Numeric(precision=20, scale=8), default=0)
    reserve_balance = db.Column(db.Numeric(precision=20, scale=8), default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'currency': self.currency,
            'total_balance': float(self.total_balance),
            'total_locked': float(self.total_locked),
            'reserve_balance': float(self.reserve_balance)
        }

    def __repr__(self):
        return f'<ExchangeWallet {self.currency} balance={self.total_balance}>'