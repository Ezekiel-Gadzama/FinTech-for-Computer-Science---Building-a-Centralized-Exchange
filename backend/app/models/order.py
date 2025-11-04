from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal
import uuid

from .. import db  # Relative import


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Order details
    trading_pair = db.Column(db.String(20), nullable=False, index=True)  # BTC/USDT
    order_type = db.Column(db.String(10), nullable=False)  # market, limit
    side = db.Column(db.String(4), nullable=False)  # buy, sell

    # Prices and amounts
    price = db.Column(db.Numeric(precision=20, scale=8), nullable=True)  # Null for market orders
    quantity = db.Column(db.Numeric(precision=20, scale=8), nullable=False)
    filled_quantity = db.Column(db.Numeric(precision=20, scale=8), default=0)
    remaining_quantity = db.Column(db.Numeric(precision=20, scale=8))

    # Status
    status = db.Column(db.String(20), default='pending', index=True)
    # pending, open, partially_filled, filled, cancelled, rejected

    # Fees
    fee = db.Column(db.Numeric(precision=20, scale=8), default=0)
    fee_currency = db.Column(db.String(10))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)

    # Relationships
    trades = db.relationship('Trade', backref='order', lazy='dynamic', foreign_keys='Trade.maker_order_id')

    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        self.remaining_quantity = self.quantity

    @property
    def is_filled(self):
        """Check if order is completely filled"""
        return self.filled_quantity >= self.quantity

    @property
    def fill_percentage(self):
        """Calculate fill percentage"""
        if self.quantity == 0:
            return 0
        return float((self.filled_quantity / self.quantity) * 100)

    def update_fill(self, quantity, price=None):
        """Update order fill information"""
        quantity = Decimal(str(quantity))
        self.filled_quantity += quantity
        self.remaining_quantity = self.quantity - self.filled_quantity

        if self.is_filled:
            self.status = 'filled'
            self.filled_at = datetime.utcnow()
        elif self.filled_quantity > 0:
            self.status = 'partially_filled'

        self.updated_at = datetime.utcnow()

    def cancel(self):
        """Cancel the order"""
        if self.status in ['pending', 'open', 'partially_filled']:
            self.status = 'cancelled'
            self.cancelled_at = datetime.utcnow()
            return True
        return False

    def to_dict(self):
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'trading_pair': self.trading_pair,
            'order_type': self.order_type,
            'side': self.side,
            'price': float(self.price) if self.price else None,
            'quantity': float(self.quantity),
            'filled_quantity': float(self.filled_quantity),
            'remaining_quantity': float(self.remaining_quantity),
            'status': self.status,
            'fill_percentage': self.fill_percentage,
            'fee': float(self.fee),
            'fee_currency': self.fee_currency,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'filled_at': self.filled_at.isoformat() if self.filled_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }

    def __repr__(self):
        return f'<Order {self.order_id} {self.side} {self.quantity} {self.trading_pair}>'


class Trade(db.Model):
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # Orders involved
    maker_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    taker_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    # Trade details
    trading_pair = db.Column(db.String(20), nullable=False, index=True)
    price = db.Column(db.Numeric(precision=20, scale=8), nullable=False)
    quantity = db.Column(db.Numeric(precision=20, scale=8), nullable=False)

    # Fees
    maker_fee = db.Column(db.Numeric(precision=20, scale=8), default=0)
    taker_fee = db.Column(db.Numeric(precision=20, scale=8), default=0)

    # Timestamp
    executed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        """Convert trade to dictionary"""
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'maker_order_id': self.maker_order_id,
            'taker_order_id': self.taker_order_id,
            'trading_pair': self.trading_pair,
            'price': float(self.price),
            'quantity': float(self.quantity),
            'maker_fee': float(self.maker_fee),
            'taker_fee': float(self.taker_fee),
            'executed_at': self.executed_at.isoformat()
        }

    def __repr__(self):
        return f'<Trade {self.trade_id} {self.quantity}@{self.price}>'
