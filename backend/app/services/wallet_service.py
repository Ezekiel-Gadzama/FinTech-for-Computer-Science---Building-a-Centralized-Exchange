from decimal import Decimal
from app import db
from app.models.wallet import Wallet, ExchangeWallet
from app.models.transaction import Transaction
from app.models.user import User


class WalletService:
    """Service for wallet operations"""

    @staticmethod
    def get_or_create_wallet(user_id: int, currency: str) -> Wallet:
        """Get existing wallet or create new one"""
        wallet = Wallet.query.filter_by(
            user_id=user_id,
            currency=currency
        ).first()

        if not wallet:
            wallet = Wallet(user_id=user_id, currency=currency)
            db.session.add(wallet)
            db.session.commit()

        return wallet

    @staticmethod
    def deposit(user_id: int, currency: str, amount: Decimal, description: str = None) -> Transaction:
        """Process deposit"""
        wallet = WalletService.get_or_create_wallet(user_id, currency)
        wallet.add_balance(amount)

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            transaction_type='deposit',
            currency=currency,
            amount=amount,
            status='completed',
            description=description or f'Deposit of {amount} {currency}'
        )
        transaction.complete()

        db.session.add(transaction)
        db.session.commit()

        return transaction

    @staticmethod
    def withdraw(user_id: int, currency: str, amount: Decimal, address: str) -> Transaction:
        """Process withdrawal"""
        wallet = WalletService.get_or_create_wallet(user_id, currency)

        if wallet.available_balance < amount:
            raise ValueError("Insufficient balance")

        wallet.deduct_balance(amount)

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            transaction_type='withdraw',
            currency=currency,
            amount=amount,
            status='completed',
            description=f'Withdrawal of {amount} {currency}',
            blockchain_address=address
        )
        transaction.complete()

        db.session.add(transaction)
        db.session.commit()

        return transaction

    @staticmethod
    def get_total_balance(user_id: int) -> dict:
        """Get total balance across all currencies"""
        wallets = Wallet.query.filter_by(user_id=user_id).all()
        return {
            wallet.currency: {
                'balance': float(wallet.balance),
                'available': float(wallet.available_balance),
                'locked': float(wallet.locked_balance)
            }
            for wallet in wallets
        }


wallet_service = WalletService()