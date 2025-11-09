from decimal import Decimal
from app import db
from app.models.wallet import Wallet, ExchangeWallet
from app.models.transaction import Transaction
from app.models.user import User
from app.models.cold_wallet import ColdWallet, ColdWalletTransfer
from datetime import datetime
import threading


class WalletService:
    """Service for wallet operations with hot/cold wallet management"""

    # Lock for thread-safe operations
    _lock = threading.Lock()

    @staticmethod
    def get_or_create_wallet(user_id: int, currency: str, wallet_type: str = 'hot') -> Wallet:
        """Get existing wallet or create new one"""
        wallet = Wallet.query.filter_by(
            user_id=user_id,
            currency=currency
        ).first()

        if not wallet:
            wallet = Wallet(user_id=user_id, currency=currency, wallet_type=wallet_type)
            db.session.add(wallet)
            db.session.commit()

        return wallet

    @staticmethod
    def get_or_create_cold_wallet(currency: str) -> ColdWallet:
        """Get or create cold wallet for a currency"""
        cold_wallet = ColdWallet.query.filter_by(currency=currency).first()
        
        if not cold_wallet:
            # In production, generate actual blockchain wallet
            from eth_account import Account
            account = Account.create()
            
            from app.utils.encryption import encrypt_private_key
            encrypted_key = encrypt_private_key(account.key.hex())
            
            cold_wallet = ColdWallet(
                currency=currency,
                public_address=account.address,
                private_key_encrypted=encrypted_key
            )
            db.session.add(cold_wallet)
            db.session.commit()
        
        return cold_wallet

    @staticmethod
    def transfer_to_cold_wallet(currency: str, amount: Decimal) -> ColdWalletTransfer:
        """Transfer funds from hot wallet to cold wallet"""
        with WalletService._lock:
            # Get exchange hot wallet balance
            exchange_wallet = ExchangeWallet.query.filter_by(currency=currency).first()
            if not exchange_wallet:
                exchange_wallet = ExchangeWallet(currency=currency)
                db.session.add(exchange_wallet)
            
            if exchange_wallet.total_balance < amount:
                raise ValueError(f"Insufficient hot wallet balance for {currency}")
            
            # Deduct from hot wallet
            exchange_wallet.total_balance -= amount
            
            # Add to cold wallet
            cold_wallet = WalletService.get_or_create_cold_wallet(currency)
            cold_wallet.balance += amount
            cold_wallet.last_transfer_at = datetime.utcnow()
            
            # Create transfer record
            transfer = ColdWalletTransfer(
                cold_wallet_id=cold_wallet.id,
                transfer_type='to_cold',
                currency=currency,
                amount=amount,
                status='completed'
            )
            transfer.completed_at = datetime.utcnow()
            
            db.session.add(transfer)
            db.session.commit()
            
            return transfer

    @staticmethod
    def transfer_from_cold_wallet(currency: str, amount: Decimal) -> ColdWalletTransfer:
        """Transfer funds from cold wallet to hot wallet (requires manual approval)"""
        with WalletService._lock:
            cold_wallet = ColdWallet.query.filter_by(currency=currency).first()
            
            if not cold_wallet:
                raise ValueError(f"No cold wallet found for {currency}")
            
            if cold_wallet.is_locked:
                raise ValueError(f"Cold wallet for {currency} is locked")
            
            if cold_wallet.balance < amount:
                raise ValueError(f"Insufficient cold wallet balance for {currency}")
            
            # Create pending transfer (requires manual approval in production)
            transfer = ColdWalletTransfer(
                cold_wallet_id=cold_wallet.id,
                transfer_type='from_cold',
                currency=currency,
                amount=amount,
                status='pending'  # Requires manual approval
            )
            
            db.session.add(transfer)
            db.session.commit()
            
            # In production, this would require multi-signature approval
            # For now, auto-approve if amount is below threshold
            if amount <= cold_wallet.min_transfer_amount:
                WalletService._execute_cold_to_hot_transfer(transfer)
            
            return transfer

    @staticmethod
    def _execute_cold_to_hot_transfer(transfer: ColdWalletTransfer):
        """Execute a cold to hot wallet transfer"""
        cold_wallet = transfer.cold_wallet
        exchange_wallet = ExchangeWallet.query.filter_by(currency=transfer.currency).first()
        
        if not exchange_wallet:
            exchange_wallet = ExchangeWallet(currency=transfer.currency)
            db.session.add(exchange_wallet)
        
        # Deduct from cold wallet
        cold_wallet.balance -= transfer.amount
        cold_wallet.last_transfer_at = datetime.utcnow()
        
        # Add to hot wallet
        exchange_wallet.total_balance += transfer.amount
        
        # Update transfer
        transfer.status = 'completed'
        transfer.completed_at = datetime.utcnow()
        
        db.session.commit()

    @staticmethod
    def auto_manage_hot_cold_balance(currency: str):
        """Automatically manage hot/cold wallet balance based on thresholds"""
        exchange_wallet = ExchangeWallet.query.filter_by(currency=currency).first()
        if not exchange_wallet:
            return
        
        cold_wallet = WalletService.get_or_create_cold_wallet(currency)
        
        # If hot wallet exceeds threshold, transfer excess to cold
        if exchange_wallet.total_balance > cold_wallet.hot_wallet_threshold:
            excess = exchange_wallet.total_balance - cold_wallet.hot_wallet_threshold
            if excess >= cold_wallet.min_transfer_amount:
                try:
                    WalletService.transfer_to_cold_wallet(currency, excess)
                except Exception as e:
                    print(f"Auto-transfer to cold wallet failed: {e}")

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