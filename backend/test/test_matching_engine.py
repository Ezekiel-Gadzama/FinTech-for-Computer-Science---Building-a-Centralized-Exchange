import pytest
import sys
import os
from decimal import Decimal
import time

# Add the parent directory to Python path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import create_app, db
from app.models.user import User
from app.models.wallet import Wallet
from app.models.order import Order
from app.services.matching_engine import matching_engine


@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def init_db(app):
    """Initialize database with test data"""
    with app.app_context():
        # Create test users
        buyer = User(email='buyer@test.com', username='buyer', password='test123')
        seller = User(email='seller@test.com', username='seller', password='test123')
        db.session.add_all([buyer, seller])
        db.session.commit()

        # Create wallets
        buyer_wallet = Wallet(user_id=buyer.id, currency='USDT', balance=10000)
        seller_wallet = Wallet(user_id=seller.id, currency='BTC', balance=1)
        db.session.add_all([buyer_wallet, seller_wallet])
        db.session.commit()

        yield db

        # Cleanup
        db.session.remove()


def test_fifo_matching(app, init_db):
    """Test FIFO order matching"""
    with app.app_context():
        # Get users (they should be created by the init_db fixture)
        buyer = User.query.filter_by(username='buyer').first()
        seller = User.query.filter_by(username='seller').first()

        # Create orders
        sell_order = Order(
            user_id=seller.id,
            trading_pair='BTC/USDT',
            order_type='limit',
            side='sell',
            price=Decimal('45000'),
            quantity=Decimal('0.1')
        )

        buy_order = Order(
            user_id=buyer.id,
            trading_pair='BTC/USDT',
            order_type='limit',
            side='buy',
            price=Decimal('45000'),
            quantity=Decimal('0.1')
        )

        db.session.add_all([sell_order, buy_order])
        db.session.commit()

        # Add to matching engine
        matching_engine.add_order(sell_order)
        matching_engine.add_order(buy_order)

        # Wait for matching
        time.sleep(2)  # Give more time for matching

        # Refresh orders from database
        db.session.refresh(sell_order)
        db.session.refresh(buy_order)

        assert sell_order.status == 'filled'
        assert buy_order.status == 'filled'
        assert sell_order.filled_quantity == Decimal('0.1')
        assert buy_order.filled_quantity == Decimal('0.1')


def test_partial_fill(app, init_db):
    """Test partial order filling"""
    with app.app_context():
        buyer = User.query.filter_by(username='buyer').first()
        seller = User.query.filter_by(username='seller').first()

        # Create a large sell order and small buy order
        sell_order = Order(
            user_id=seller.id,
            trading_pair='BTC/USDT',
            order_type='limit',
            side='sell',
            price=Decimal('45000'),
            quantity=Decimal('1.0')  # Large quantity
        )

        buy_order = Order(
            user_id=buyer.id,
            trading_pair='BTC/USDT',
            order_type='limit',
            side='buy',
            price=Decimal('45000'),
            quantity=Decimal('0.1')  # Small quantity
        )

        db.session.add_all([sell_order, buy_order])
        db.session.commit()

        # Add to matching engine
        matching_engine.add_order(sell_order)
        matching_engine.add_order(buy_order)

        # Wait for matching
        time.sleep(2)

        # Refresh orders
        db.session.refresh(sell_order)
        db.session.refresh(buy_order)

        # Buy order should be filled, sell order should be partially filled
        assert buy_order.status == 'filled'
        assert sell_order.status == 'partially_filled'
        assert sell_order.filled_quantity == Decimal('0.1')
        assert sell_order.remaining_quantity == Decimal('0.9')


def test_order_cancellation(app, init_db):
    """Test order cancellation"""
    with app.app_context():
        buyer = User.query.filter_by(username='buyer').first()

        # Create an order
        buy_order = Order(
            user_id=buyer.id,
            trading_pair='BTC/USDT',
            order_type='limit',
            side='buy',
            price=Decimal('45000'),
            quantity=Decimal('0.1')
        )

        db.session.add(buy_order)
        db.session.commit()

        # Add to matching engine
        matching_engine.add_order(buy_order)

        # Wait a bit
        time.sleep(0.5)

        # Cancel the order
        success = matching_engine.cancel_order(buy_order.order_id)

        assert success == True

        # Refresh and check status
        db.session.refresh(buy_order)
        assert buy_order.status == 'cancelled'


if __name__ == '__main__':
    pytest.main([__file__])