"""Public API routes for third-party integrations"""
from flask import Blueprint, request, jsonify, g
from .. import db
from ..models.order import Order, Trade
from ..models.wallet import Wallet
from ..models.transaction import Transaction
from ..middleware.api_auth import require_api_key, require_api_permission
from ..services.matching_engine import matching_engine
from decimal import Decimal

bp = Blueprint('api', __name__, url_prefix='/api/v1')


@bp.route('/account/balance', methods=['GET'])
@require_api_key
@require_api_permission('read')
def get_balance():
    """Get account balance (API)"""
    try:
        user_id = g.user_id
        wallets = Wallet.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'balances': [wallet.to_dict() for wallet in wallets]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/orders', methods=['GET'])
@require_api_key
@require_api_permission('read')
def get_orders():
    """Get orders (API)"""
    try:
        user_id = g.user_id
        status = request.args.get('status')
        trading_pair = request.args.get('pair')
        limit = int(request.args.get('limit', 50))
        
        query = Order.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        if trading_pair:
            query = query.filter_by(trading_pair=trading_pair)
        
        orders = query.order_by(Order.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/orders', methods=['POST'])
@require_api_key
@require_api_permission('trade')
def place_order():
    """Place order (API)"""
    try:
        from ..routes.trading import place_order as internal_place_order
        
        # Use internal order placement logic
        user_id = g.user_id
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['trading_pair', 'side', 'quantity']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Parse data
        trading_pair = data['trading_pair']
        side = data['side'].lower()
        order_type = data.get('order_type', 'limit').lower()
        quantity = Decimal(str(data['quantity']))
        price = Decimal(str(data['price'])) if 'price' in data and data['price'] else None
        
        # Validate
        if side not in ['buy', 'sell']:
            return jsonify({'error': 'Invalid side'}), 400
        
        if order_type not in ['market', 'limit']:
            return jsonify({'error': 'Invalid order type'}), 400
        
        if order_type == 'limit' and not price:
            return jsonify({'error': 'Price required for limit orders'}), 400
        
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be positive'}), 400
        
        # Get currencies
        base_currency, quote_currency = trading_pair.split('/')
        
        # Check and lock balance
        if side == 'buy':
            required_amount = quantity * (price if price else Decimal('0'))
            wallet = Wallet.query.filter_by(
                user_id=user_id,
                currency=quote_currency
            ).first()
        else:
            required_amount = quantity
            wallet = Wallet.query.filter_by(
                user_id=user_id,
                currency=base_currency
            ).first()
        
        if not wallet or wallet.available_balance < required_amount:
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Lock the balance
        if not wallet.lock_balance(required_amount):
            return jsonify({'error': 'Failed to lock balance'}), 500
        
        # Create order
        order = Order(
            user_id=user_id,
            trading_pair=trading_pair,
            order_type=order_type,
            side=side,
            price=price,
            quantity=quantity,
            fee_currency=quote_currency
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Submit to matching engine
        matching_engine.add_order(order)
        
        return jsonify({
            'order': order.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid number format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/orders/<order_id>', methods=['DELETE'])
@require_api_key
@require_api_permission('trade')
def cancel_order(order_id):
    """Cancel order (API)"""
    try:
        user_id = g.user_id
        
        order = Order.query.filter_by(
            order_id=order_id,
            user_id=user_id
        ).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order.status not in ['open', 'partially_filled']:
            return jsonify({'error': 'Cannot cancel this order'}), 400
        
        # Cancel via matching engine
        if matching_engine.cancel_order(order_id):
            return jsonify({
                'message': 'Order cancelled successfully',
                'order': order.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Failed to cancel order'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/orderbook', methods=['GET'])
@require_api_key
@require_api_permission('read')
def get_orderbook():
    """Get order book (API)"""
    try:
        pair = request.args.get('pair')
        if not pair:
            return jsonify({'error': 'Pair parameter required'}), 400
        
        depth = int(request.args.get('depth', 20))
        orderbook = matching_engine.get_orderbook(pair, depth)
        
        return jsonify({
            'pair': pair,
            'orderbook': orderbook
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/trades', methods=['GET'])
@require_api_key
@require_api_permission('read')
def get_trades():
    """Get recent trades (API)"""
    try:
        pair = request.args.get('pair')
        if not pair:
            return jsonify({'error': 'Pair parameter required'}), 400
        
        limit = int(request.args.get('limit', 50))
        
        trades = Trade.query.filter_by(trading_pair=pair) \
            .order_by(Trade.executed_at.desc()) \
            .limit(limit) \
            .all()
        
        return jsonify({
            'pair': pair,
            'trades': [trade.to_dict() for trade in trades]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

