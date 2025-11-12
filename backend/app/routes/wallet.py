from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.wallet import Wallet
from ..models.transaction import Transaction
from decimal import Decimal

bp = Blueprint('wallet', __name__, url_prefix='/api/wallet')


@bp.route('/balances', methods=['GET'])
@jwt_required()
def get_balances():
    """Get user's wallet balances"""
    try:
        current_user_id = get_jwt_identity()

        wallets = Wallet.query.filter_by(user_id=current_user_id).all()

        return jsonify({
            'balances': [wallet.to_dict() for wallet in wallets]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/balance/<currency>', methods=['GET'])
@jwt_required()
def get_balance(currency):
    """Get balance for specific currency"""
    try:
        current_user_id = get_jwt_identity()

        wallet = Wallet.query.filter_by(
            user_id=current_user_id,
            currency=currency.upper()
        ).first()

        if not wallet:
            return jsonify({'error': 'Wallet not found'}), 404

        return jsonify({'balance': wallet.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    """Simulate a deposit (for testing)"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not all(k in data for k in ['currency', 'amount']):
            return jsonify({'error': 'Missing required fields'}), 400

        currency = data['currency'].upper()
        amount = Decimal(str(data['amount']))

        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400

        # Get or create wallet
        wallet = Wallet.query.filter_by(
            user_id=current_user_id,
            currency=currency
        ).first()

        if not wallet:
            wallet = Wallet(
                user_id=current_user_id,
                currency=currency
            )
            db.session.add(wallet)

        # Add balance
        wallet.add_balance(amount)

        # Create transaction record
        transaction = Transaction(
            user_id=current_user_id,
            transaction_type='deposit',
            currency=currency,
            amount=amount,
            status='completed',
            description=f'Deposit of {amount} {currency}'
        )
        transaction.complete()

        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            'message': 'Deposit successful',
            'wallet': wallet.to_dict(),
            'transaction': transaction.to_dict()
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid amount: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw():
    """Process a withdrawal"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not all(k in data for k in ['currency', 'amount', 'address']):
            return jsonify({'error': 'Missing required fields'}), 400

        currency = data['currency'].upper()
        amount = Decimal(str(data['amount']))
        address = data['address']

        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400

        # Get wallet
        wallet = Wallet.query.filter_by(
            user_id=current_user_id,
            currency=currency
        ).first()

        if not wallet:
            return jsonify({'error': 'Wallet not found'}), 404

        if wallet.available_balance < amount:
            return jsonify({'error': 'Insufficient balance'}), 400

        # Deduct balance
        if not wallet.deduct_balance(amount):
            return jsonify({'error': 'Failed to deduct balance'}), 500

        # Create transaction record
        transaction = Transaction(
            user_id=current_user_id,
            transaction_type='withdraw',
            currency=currency,
            amount=amount,
            status='pending',
            description=f'Withdrawal of {amount} {currency}',
            blockchain_address=address
        )

        db.session.add(transaction)
        db.session.commit()

        # In production, this would trigger actual blockchain transaction
        # For now, mark as completed immediately
        transaction.complete()
        db.session.commit()

        return jsonify({
            'message': 'Withdrawal processed',
            'wallet': wallet.to_dict(),
            'transaction': transaction.to_dict()
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid amount: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get user's transaction history"""
    try:
        current_user_id = get_jwt_identity()

        # Query parameters
        transaction_type = request.args.get('type')
        currency = request.args.get('currency')
        limit = int(request.args.get('limit', 50))

        # Build query
        query = Transaction.query.filter_by(user_id=current_user_id)

        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)

        if currency:
            query = query.filter_by(currency=currency.upper())

        transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()

        return jsonify({
            'transactions': [tx.to_dict() for tx in transactions]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/transaction/<transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get specific transaction details"""
    try:
        current_user_id = get_jwt_identity()

        transaction = Transaction.query.filter_by(
            transaction_id=transaction_id,
            user_id=current_user_id
        ).first()

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        return jsonify({'transaction': transaction.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/address/<currency>', methods=['GET'])
@jwt_required()
def get_deposit_address(currency):
    """Get deposit address for a currency"""
    try:
        current_user_id = get_jwt_identity()

        from ..models.user import User
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Return user's public address (simplified - in production, generate per-currency)
        return jsonify({
            'currency': currency.upper(),
            'address': user.public_address
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500