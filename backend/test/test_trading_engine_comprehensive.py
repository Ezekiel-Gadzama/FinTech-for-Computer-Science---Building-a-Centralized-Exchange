"""
Comprehensive tests for the trading engine covering FIFO and Pro-Rata algorithms
"""
import pytest
import sys
import os
from decimal import Decimal

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from app.models.wallet import Wallet
from app.models.order import Order
from app.services.matching_engine import OrderMatchingEngine


@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_users(app):
    """Create test users with wallets"""
    with app.app_context():
        buyer = User(email='buyer@test.com', username='buyer', password='test123')
        seller = User(email='seller@test.com', username='seller', password='test123')
        db.session.add_all([buyer, seller])
        db.session.commit()

        # Create wallets with balances
        buyer_usdt = Wallet(user_id=buyer.id, currency='USDT', balance=100000)
        seller_btc = Wallet(user_id=seller.id, currency='BTC', balance=10)
        seller_usdt = Wallet(user_id=seller.id, currency='USDT', balance=50000)
        buyer_btc = Wallet(user_id=buyer.id, currency='BTC', balance=1)

        db.session.add_all([buyer_usdt, seller_btc, seller_usdt, buyer_btc])
        db.session.commit()

        return {
            'buyer_id': buyer.id,
            'seller_id': seller.id,
        }


class TestFIFOMatching:
    """Test FIFO matching algorithm"""

    def test_fifo_exact_match(self, app, test_users):
        """Test FIFO matching with exact quantity match"""
        with app.app_context():
            buyer = User.query.get(test_users['buyer_id'])
            seller = User.query.get(test_users['seller_id'])
            seller_btc = Wallet.query.filter_by(user_id=seller.id, currency='BTC').first()
            buyer_usdt = Wallet.query.filter_by(user_id=buyer.id, currency='USDT').first()
            buyer_btc = Wallet.query.filter_by(user_id=buyer.id, currency='BTC').first()
            seller_usdt = Wallet.query.filter_by(user_id=seller.id, currency='USDT').first()

            engine = OrderMatchingEngine(matching_algorithm='FIFO')

            # Create and add sell order first
            sell_order = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('50000'),
                quantity=Decimal('0.5')
            )
            db.session.add(sell_order)
            db.session.commit()

            # Lock balance for sell order
            seller_btc.lock_balance(Decimal('0.5'))
            db.session.commit()

            # Process sell order - it will be added to order book since no matching buy orders
            engine._match_order(sell_order)
            db.session.commit()
            db.session.refresh(sell_order)
            
            # Verify sell order is in the book (status should be 'open')
            assert sell_order.status == 'open'
            assert len(engine.order_books['BTC/USDT']['asks']) == 1

            # Create and add buy order
            buy_order = Order(
                user_id=buyer.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='buy',
                price=Decimal('50000'),
                quantity=Decimal('0.5')
            )
            db.session.add(buy_order)
            db.session.commit()

            # Lock balance for buy order
            buyer_usdt.lock_balance(Decimal('25000'))
            db.session.commit()

            # Process buy order - it should match against the sell order
            engine._match_order(buy_order)
            db.session.commit()

            # Refresh orders
            db.session.refresh(sell_order)
            db.session.refresh(buy_order)

            assert sell_order.status == 'filled'
            assert buy_order.status == 'filled'
            assert sell_order.filled_quantity == Decimal('0.5')
            assert buy_order.filled_quantity == Decimal('0.5')

            # Check wallets
            db.session.refresh(seller_btc)
            db.session.refresh(buyer_usdt)
            db.session.refresh(buyer_btc)
            db.session.refresh(seller_usdt)

            assert buyer_btc.balance == Decimal('1.5')  # 1 + 0.5
            assert seller_usdt.balance > Decimal('50000')  # Received USDT minus fee

    def test_fifo_partial_fill(self, app, test_users):
        """Test FIFO matching with partial fill"""
        with app.app_context():
            buyer = User.query.get(test_users['buyer_id'])
            seller = User.query.get(test_users['seller_id'])

            engine = OrderMatchingEngine(matching_algorithm='FIFO')

            # Create large sell order first
            sell_order = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('50000'),
                quantity=Decimal('2.0')
            )
            db.session.add(sell_order)
            db.session.commit()

            # Lock balances
            seller_btc = Wallet.query.filter_by(user_id=seller.id, currency='BTC').first()
            buyer_usdt = Wallet.query.filter_by(user_id=buyer.id, currency='USDT').first()
            seller_btc.lock_balance(Decimal('2.0'))
            buyer_usdt.lock_balance(Decimal('15000'))
            db.session.commit()

            # Process sell order - will be added to book
            engine._match_order(sell_order)
            db.session.commit()
            db.session.refresh(sell_order)
            assert sell_order.status == 'open'

            # Create small buy order
            buy_order = Order(
                user_id=buyer.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='buy',
                price=Decimal('50000'),
                quantity=Decimal('0.3')
            )
            db.session.add(buy_order)
            db.session.commit()

            # Process buy order - should match partially with sell order
            engine._match_order(buy_order)
            db.session.commit()

            db.session.refresh(sell_order)
            db.session.refresh(buy_order)

            # Buy order should be filled, sell order should be partially filled
            assert buy_order.status == 'filled'
            assert sell_order.status == 'partially_filled'
            assert sell_order.filled_quantity == Decimal('0.3')
            assert sell_order.remaining_quantity == Decimal('1.7')

    def test_fifo_price_priority(self, app, test_users):
        """Test FIFO respects price priority"""
        with app.app_context():
            buyer = User.query.get(test_users['buyer_id'])
            seller = User.query.get(test_users['seller_id'])
            
            engine = OrderMatchingEngine(matching_algorithm='FIFO')

            # Create multiple sell orders at different prices
            sell1 = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('49000'),
                quantity=Decimal('0.1')
            )
            sell2 = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('50000'),
                quantity=Decimal('0.1')
            )
            db.session.add_all([sell1, sell2])
            db.session.commit()

            # Lock balances
            seller_btc = Wallet.query.filter_by(user_id=seller.id, currency='BTC').first()
            buyer_usdt = Wallet.query.filter_by(user_id=buyer.id, currency='USDT').first()
            seller_btc.lock_balance(Decimal('0.2'))
            buyer_usdt.lock_balance(Decimal('10200'))
            db.session.commit()

            # Add sell orders to book
            engine._match_order(sell1)
            db.session.commit()
            engine._match_order(sell2)
            db.session.commit()
            db.session.refresh(sell1)
            db.session.refresh(sell2)
            assert sell1.status == 'open'
            assert sell2.status == 'open'

            # Create buy order that should match with lower price first
            buy_order = Order(
                user_id=buyer.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='buy',
                price=Decimal('51000'),
                quantity=Decimal('0.2')
            )
            db.session.add(buy_order)
            db.session.commit()

            # Process buy order - should match both sell orders (lower price first)
            engine._match_order(buy_order)
            db.session.commit()

            db.session.refresh(sell1)
            db.session.refresh(sell2)
            db.session.refresh(buy_order)

            # Should match with lower price first (sell1), then sell2
            assert sell1.status == 'filled'
            assert sell2.status == 'filled'
            assert buy_order.status == 'filled'


class TestProRataMatching:
    """Test Pro-Rata matching algorithm"""

    def test_pro_rata_proportional_allocation(self, app, test_users):
        """Test Pro-Rata allocates proportionally across multiple orders"""
        with app.app_context():
            buyer = User.query.get(test_users['buyer_id'])
            seller = User.query.get(test_users['seller_id'])
            
            engine = OrderMatchingEngine(matching_algorithm='PRO_RATA')

            # Create multiple sell orders at same price
            sell1 = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('50000'),
                quantity=Decimal('0.5')
            )
            sell2 = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('50000'),
                quantity=Decimal('1.0')
            )
            sell3 = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('50000'),
                quantity=Decimal('0.5')
            )
            db.session.add_all([sell1, sell2, sell3])
            db.session.commit()

            # Lock balances
            seller_btc = Wallet.query.filter_by(user_id=seller.id, currency='BTC').first()
            buyer_usdt = Wallet.query.filter_by(user_id=buyer.id, currency='USDT').first()
            seller_btc.lock_balance(Decimal('2.0'))
            buyer_usdt.lock_balance(Decimal('50000'))
            db.session.commit()

            # Add sell orders to book
            engine._match_order(sell1)
            db.session.commit()
            engine._match_order(sell2)
            db.session.commit()
            engine._match_order(sell3)
            db.session.commit()

            # Create buy order that partially fills all
            buy_order = Order(
                user_id=buyer.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='buy',
                price=Decimal('50000'),
                quantity=Decimal('1.0')  # Will be distributed proportionally
            )
            db.session.add(buy_order)
            db.session.commit()

            # Process buy order
            engine._match_order(buy_order)
            db.session.commit()

            db.session.refresh(sell1)
            db.session.refresh(sell2)
            db.session.refresh(sell3)
            db.session.refresh(buy_order)

            # All should be partially filled proportionally
            total_filled = sell1.filled_quantity + sell2.filled_quantity + sell3.filled_quantity
            assert abs(total_filled - Decimal('1.0')) < Decimal('0.01')  # Allow small rounding
            assert buy_order.status == 'filled'

            # Proportions should be maintained
            # sell1: 0.5/2.0 = 25%, sell2: 1.0/2.0 = 50%, sell3: 0.5/2.0 = 25%
            assert abs(sell1.filled_quantity - Decimal('0.25')) < Decimal('0.1')
            assert abs(sell2.filled_quantity - Decimal('0.5')) < Decimal('0.1')
            assert abs(sell3.filled_quantity - Decimal('0.25')) < Decimal('0.1')

    def test_pro_rata_price_level_priority(self, app, test_users):
        """Test Pro-Rata only matches orders at best price level"""
        with app.app_context():
            buyer = User.query.get(test_users['buyer_id'])
            seller = User.query.get(test_users['seller_id'])
            
            engine = OrderMatchingEngine(matching_algorithm='PRO_RATA')

            # Create orders at different price levels
            sell1 = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('49000'),  # Best price
                quantity=Decimal('0.5')
            )
            sell2 = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('50000'),  # Worse price
                quantity=Decimal('0.5')
            )
            db.session.add_all([sell1, sell2])
            db.session.commit()

            # Lock balances
            seller_btc = Wallet.query.filter_by(user_id=seller.id, currency='BTC').first()
            buyer_usdt = Wallet.query.filter_by(user_id=buyer.id, currency='USDT').first()
            seller_btc.lock_balance(Decimal('1.0'))
            buyer_usdt.lock_balance(Decimal('15300'))
            db.session.commit()

            # Add sell orders to book
            engine._match_order(sell1)
            db.session.commit()
            engine._match_order(sell2)
            db.session.commit()
            db.session.refresh(sell1)
            db.session.refresh(sell2)
            assert sell1.status == 'open'
            assert sell2.status == 'open'

            # Create buy order that can match both but should only match best price
            buy_order = Order(
                user_id=buyer.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='buy',
                price=Decimal('51000'),
                quantity=Decimal('0.3')
            )
            db.session.add(buy_order)
            db.session.commit()

            # Process buy order
            engine._match_order(buy_order)
            db.session.commit()

            db.session.refresh(sell1)
            db.session.refresh(sell2)
            db.session.refresh(buy_order)

            # Should only match with best price (sell1)
            assert sell1.status in ['filled', 'partially_filled']
            assert sell2.status == 'open'  # Should not be matched
            assert buy_order.status == 'filled'


class TestMarketOrders:
    """Test market order matching"""

    def test_market_order_immediate_fill(self, app, test_users):
        """Test market orders fill immediately at best available price"""
        with app.app_context():
            buyer = User.query.get(test_users['buyer_id'])
            seller = User.query.get(test_users['seller_id'])
            
            engine = OrderMatchingEngine(matching_algorithm='FIFO')

            # Create limit sell order first
            sell_order = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('50000'),
                quantity=Decimal('0.5')
            )
            db.session.add(sell_order)
            db.session.commit()

            # Lock balances
            seller_btc = Wallet.query.filter_by(user_id=seller.id, currency='BTC').first()
            buyer_usdt = Wallet.query.filter_by(user_id=buyer.id, currency='USDT').first()
            seller_btc.lock_balance(Decimal('0.5'))
            buyer_usdt.lock_balance(Decimal('20000'))  # Enough for market order
            db.session.commit()

            # Add sell order to book
            engine._match_order(sell_order)
            db.session.commit()
            db.session.refresh(sell_order)
            assert sell_order.status == 'open'

            # Create market buy order
            buy_order = Order(
                user_id=buyer.id,
                trading_pair='BTC/USDT',
                order_type='market',
                side='buy',
                quantity=Decimal('0.3')
            )
            db.session.add(buy_order)
            db.session.commit()

            # Process market order - should match immediately
            engine._match_order(buy_order)
            db.session.commit()

            db.session.refresh(sell_order)
            db.session.refresh(buy_order)

            assert buy_order.status == 'filled'
            assert sell_order.status == 'partially_filled'
            assert buy_order.filled_quantity == Decimal('0.3')


class TestOrderBook:
    """Test order book management"""

    def test_orderbook_updates(self, app, test_users):
        """Test order book is updated correctly"""
        with app.app_context():
            buyer = User.query.get(test_users['buyer_id'])
            seller = User.query.get(test_users['seller_id'])
            
            engine = OrderMatchingEngine(matching_algorithm='FIFO')

            # Create orders that won't match (prices don't overlap)
            sell_order = Order(
                user_id=seller.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='sell',
                price=Decimal('51000'),
                quantity=Decimal('0.5')
            )
            buy_order = Order(
                user_id=buyer.id,
                trading_pair='BTC/USDT',
                order_type='limit',
                side='buy',
                price=Decimal('49000'),
                quantity=Decimal('0.5')
            )
            db.session.add_all([sell_order, buy_order])
            db.session.commit()

            # Lock balances
            seller_btc = Wallet.query.filter_by(user_id=seller.id, currency='BTC').first()
            buyer_usdt = Wallet.query.filter_by(user_id=buyer.id, currency='USDT').first()
            seller_btc.lock_balance(Decimal('0.5'))
            buyer_usdt.lock_balance(Decimal('24500'))
            db.session.commit()

            # Process orders - they should be added to book but not match
            engine._match_order(sell_order)
            db.session.commit()
            engine._match_order(buy_order)
            db.session.commit()

            # Check order book
            orderbook = engine.get_orderbook('BTC/USDT')
            assert len(orderbook['bids']) > 0
            assert len(orderbook['asks']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
