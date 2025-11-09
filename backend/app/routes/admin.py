"""Admin routes for wallet management"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.cold_wallet import ColdWallet, ColdWalletTransfer
from ..models.wallet import ExchangeWallet
from ..services.wallet_service import WalletService
from ..utils.decorators import admin_required
from decimal import Decimal

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@bp.route('/cold-wallets', methods=['GET'])
@jwt_required()
@admin_required
def get_cold_wallets():
    """Get all cold wallets"""
    try:
        cold_wallets = ColdWallet.query.all()
        return jsonify({
            'cold_wallets': [cw.to_dict() for cw in cold_wallets]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/cold-wallet/<currency>', methods=['GET'])
@jwt_required()
@admin_required
def get_cold_wallet(currency):
    """Get cold wallet for specific currency"""
    try:
        cold_wallet = ColdWallet.query.filter_by(currency=currency.upper()).first()
        if not cold_wallet:
            return jsonify({'error': 'Cold wallet not found'}), 404
        
        return jsonify({'cold_wallet': cold_wallet.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/transfer/to-cold', methods=['POST'])
@jwt_required()
@admin_required
def transfer_to_cold():
    """Transfer funds to cold wallet"""
    try:
        data = request.get_json()
        currency = data.get('currency', '').upper()
        amount = Decimal(str(data.get('amount', 0)))
        
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        transfer = WalletService.transfer_to_cold_wallet(currency, amount)
        
        return jsonify({
            'message': 'Transfer to cold wallet completed',
            'transfer': transfer.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/transfer/from-cold', methods=['POST'])
@jwt_required()
@admin_required
def transfer_from_cold():
    """Transfer funds from cold wallet (requires approval)"""
    try:
        data = request.get_json()
        currency = data.get('currency', '').upper()
        amount = Decimal(str(data.get('amount', 0)))
        
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        transfer = WalletService.transfer_from_cold_wallet(currency, amount)
        
        return jsonify({
            'message': 'Transfer from cold wallet initiated',
            'transfer': transfer.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/transfer/approve/<transfer_id>', methods=['POST'])
@jwt_required()
@admin_required
def approve_cold_transfer(transfer_id):
    """Approve and execute a pending cold wallet transfer"""
    try:
        transfer = ColdWalletTransfer.query.get(transfer_id)
        if not transfer:
            return jsonify({'error': 'Transfer not found'}), 404
        
        if transfer.status != 'pending':
            return jsonify({'error': 'Transfer is not pending'}), 400
        
        if transfer.transfer_type != 'from_cold':
            return jsonify({'error': 'Can only approve from_cold transfers'}), 400
        
        WalletService._execute_cold_to_hot_transfer(transfer)
        
        return jsonify({
            'message': 'Transfer approved and executed',
            'transfer': transfer.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/transfers', methods=['GET'])
@jwt_required()
@admin_required
def get_transfers():
    """Get all cold wallet transfers"""
    try:
        currency = request.args.get('currency')
        transfer_type = request.args.get('type')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        query = ColdWalletTransfer.query
        
        if currency:
            query = query.filter_by(currency=currency.upper())
        if transfer_type:
            query = query.filter_by(transfer_type=transfer_type)
        if status:
            query = query.filter_by(status=status)
        
        transfers = query.order_by(ColdWalletTransfer.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'transfers': [t.to_dict() for t in transfers]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/exchange-wallets', methods=['GET'])
@jwt_required()
@admin_required
def get_exchange_wallets():
    """Get all exchange wallets (hot wallets)"""
    try:
        wallets = ExchangeWallet.query.all()
        return jsonify({
            'wallets': [w.to_dict() for w in wallets]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

