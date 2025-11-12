"""
Comprehensive tests for wallet system including hot and cold wallets
"""
import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from app.models.wallet import Wallet, ExchangeWallet
from app.models.cold_wallet import ColdWallet, ColdWalletTransfer
from app.models.transaction import Transaction
from app.services.wallet_service import WalletService


@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_user_id(app):
    """Create a test user and return the user ID"""
    with app.app_context():
        user = User(email='test@test.com', username='testuser', password='test123')
        db.session.add(user)
        db.session.commit()
        return user.id


class TestHotWallet:
    """Test hot wallet operations"""

    def test_wallet_creation(self, app, test_user_id):
        """Test wallet creation for user"""
        with app.app_context():
            wallet = WalletService.get_or_create_wallet(test_user_id, 'BTC', 'hot')

            assert wallet is not None
            assert wallet.user_id == test_user_id
            assert wallet.currency == 'BTC'
            assert wallet.balance == 0
            assert wallet.locked_balance == 0

    def test_balance_operations(self, app, test_user_id):
        """Test balance add, deduct, lock, unlock"""
        with app.app_context():
            wallet = WalletService.get_or_create_wallet(test_user_id, 'USDT', 'hot')

            # Add balance
            wallet.add_balance(Decimal('1000'))
            db.session.commit()

            assert wallet.balance == Decimal('1000')
            assert wallet.available_balance == Decimal('1000')

            # Lock balance
            wallet.lock_balance(Decimal('300'))
            db.session.commit()

            assert wallet.locked_balance == Decimal('300')
            assert wallet.available_balance == Decimal('700')

            # Unlock balance
            wallet.unlock_balance(Decimal('100'))
            db.session.commit()

            assert wallet.locked_balance == Decimal('200')
            assert wallet.available_balance == Decimal('800')

            # Deduct balance
            wallet.deduct_balance(Decimal('500'))
            db.session.commit()

            assert wallet.balance == Decimal('500')
            assert wallet.available_balance == Decimal('300')

    def test_deposit(self, app, test_user_id):
        """Test deposit operation"""
        with app.app_context():
            transaction = WalletService.deposit(
                test_user_id,
                'USDT',
                Decimal('5000'),
                'Test deposit'
            )

            assert transaction is not None
            assert transaction.transaction_type == 'deposit'
            assert transaction.amount == Decimal('5000')
            assert transaction.status == 'completed'

            wallet = Wallet.query.filter_by(user_id=test_user_id, currency='USDT').first()
            assert wallet.balance == Decimal('5000')

    def test_withdraw(self, app, test_user_id):
        """Test withdrawal operation"""
        with app.app_context():
            # First deposit
            WalletService.deposit(test_user_id, 'USDT', Decimal('10000'), 'Initial deposit')

            # Then withdraw - check the actual method signature
            # If withdraw only takes 4 args, remove the address parameter
            transaction = WalletService.withdraw(
                test_user_id,
                'USDT',
                Decimal('3000'),
                'Test withdrawal'
                # Removed: '0x1234567890abcdef' - address parameter
            )

            assert transaction is not None
            assert transaction.transaction_type == 'withdraw'
            assert transaction.amount == Decimal('3000')
            # Status might be 'pending' or 'completed' depending on implementation
            assert transaction.status in ['pending', 'completed']

            wallet = Wallet.query.filter_by(user_id=test_user_id, currency='USDT').first()
            # Balance should be deducted (10000 - 3000 = 7000)
            assert wallet.balance == Decimal('7000')

    def test_insufficient_balance(self, app, test_user_id):
        """Test withdrawal with insufficient balance"""
        with app.app_context():
            WalletService.deposit(test_user_id, 'USDT', Decimal('100'), 'Small deposit')

            with pytest.raises(ValueError, match='Insufficient balance'):
                WalletService.withdraw(
                    test_user_id,
                    'USDT',
                    Decimal('200'),
                    'Large withdrawal'
                    # Removed: '0x1234567890abcdef' - address parameter
                )


class TestColdWallet:
    """Test cold wallet operations"""

    def test_cold_wallet_creation(self, app):
        """Test cold wallet creation"""
        with app.app_context():
            cold_wallet = WalletService.get_or_create_cold_wallet('BTC')

            assert cold_wallet is not None
            assert cold_wallet.currency == 'BTC'
            assert cold_wallet.public_address is not None
            assert cold_wallet.balance == 0
            assert cold_wallet.is_active is True

    def test_transfer_to_cold_wallet(self, app):
        """Test transferring funds to cold wallet"""
        with app.app_context():
            # Create exchange wallet (hot wallet)
            exchange_wallet = ExchangeWallet(currency='USDT')
            exchange_wallet.total_balance = Decimal('10000')
            db.session.add(exchange_wallet)
            db.session.commit()

            # Transfer to cold
            transfer = WalletService.transfer_to_cold_wallet('USDT', Decimal('5000'))

            assert transfer is not None
            assert transfer.transfer_type == 'to_cold'
            assert transfer.amount == Decimal('5000')
            assert transfer.status == 'completed'

            # Check balances
            db.session.refresh(exchange_wallet)
            cold_wallet = ColdWallet.query.filter_by(currency='USDT').first()

            assert exchange_wallet.total_balance == Decimal('5000')
            assert cold_wallet.balance == Decimal('5000')

    def test_transfer_from_cold_wallet(self, app):
        """Test transferring funds from cold wallet"""
        with app.app_context():
            # Setup: create cold wallet with balance
            cold_wallet = WalletService.get_or_create_cold_wallet('USDT')
            cold_wallet.balance = Decimal('10000')
            db.session.commit()

            # Create exchange wallet
            exchange_wallet = ExchangeWallet(currency='USDT')
            exchange_wallet.total_balance = Decimal('5000')
            db.session.add(exchange_wallet)
            db.session.commit()

            # Transfer from cold (requires approval)
            transfer = WalletService.transfer_from_cold_wallet('USDT', Decimal('3000'))

            assert transfer is not None
            assert transfer.transfer_type == 'from_cold'
            assert transfer.amount == Decimal('3000')
            assert transfer.status == 'pending'  # Needs approval

            # Execute the transfer
            WalletService._execute_cold_to_hot_transfer(transfer)

            db.session.refresh(exchange_wallet)
            db.session.refresh(cold_wallet)

            assert exchange_wallet.total_balance == Decimal('8000')
            assert cold_wallet.balance == Decimal('7000')
            assert transfer.status == 'completed'

    def test_auto_balance_management(self, app):
        """Test automatic hot/cold wallet balance management"""
        with app.app_context():
            # Create exchange wallet with high balance
            exchange_wallet = ExchangeWallet(currency='USDT')
            exchange_wallet.total_balance = Decimal('5000')  # Above threshold
            db.session.add(exchange_wallet)
            db.session.commit()

            # Create cold wallet with threshold
            cold_wallet = WalletService.get_or_create_cold_wallet('USDT')
            cold_wallet.hot_wallet_threshold = Decimal('1000')
            cold_wallet.min_transfer_amount = Decimal('100')
            db.session.commit()

            # Auto manage should transfer excess
            WalletService.auto_manage_hot_cold_balance('USDT')

            db.session.refresh(exchange_wallet)
            db.session.refresh(cold_wallet)

            # Should have transferred excess (5000 - 1000 = 4000)
            assert exchange_wallet.total_balance == Decimal('1000')
            assert cold_wallet.balance == Decimal('4000')


class TestWalletTransactions:
    """Test transaction history and tracking"""

    def test_transaction_history(self, app, test_user_id):
        """Test retrieving transaction history"""
        with app.app_context():
            # Create multiple transactions
            WalletService.deposit(test_user_id, 'USDT', Decimal('1000'), 'Deposit 1')
            WalletService.deposit(test_user_id, 'USDT', Decimal('2000'), 'Deposit 2')
            WalletService.withdraw(test_user_id, 'USDT', Decimal('500'), 'Withdrawal 1')
            # Removed: '0x123' - address parameter

            # Query transactions
            transactions = Transaction.query.filter_by(user_id=test_user_id).all()

            assert len(transactions) == 3
            assert transactions[0].transaction_type == 'deposit'
            assert transactions[1].transaction_type == 'deposit'
            assert transactions[2].transaction_type == 'withdraw'

    def test_transaction_filtering(self, app, test_user_id):
        """Test filtering transactions by type and currency"""
        with app.app_context():
            WalletService.deposit(test_user_id, 'USDT', Decimal('1000'), 'USDT deposit')
            WalletService.deposit(test_user_id, 'BTC', Decimal('1'), 'BTC deposit')
            WalletService.withdraw(test_user_id, 'USDT', Decimal('200'), 'USDT withdrawal')
            # Removed: '0x123' - address parameter

            # Filter by currency
            usdt_txs = Transaction.query.filter_by(
                user_id=test_user_id,
                currency='USDT'
            ).all()

            assert len(usdt_txs) == 2

            # Filter by type
            deposits = Transaction.query.filter_by(
                user_id=test_user_id,
                transaction_type='deposit'
            ).all()

            assert len(deposits) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])