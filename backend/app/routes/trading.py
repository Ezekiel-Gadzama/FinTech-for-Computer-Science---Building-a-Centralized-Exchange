from .. import db
from ..models.order import Order, Trade
from ..models.wallet import Wallet
from ..services.matching_engine import matching_engine
from decimal import Decimal
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('trading', __name__, url_prefix='/api/trading')


@bp.route('/order', methods=['POST'])
@jwt_required()
def place_order():
    """Place a new order"""
    try:
        current_user_id = get_jwt_identity()
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
            # For buy orders, lock quote currency
            required_amount = quantity * (price if price else _get_market_price(trading_pair, 'ask'))
            wallet = Wallet.query.filter_by(
                user_id=current_user_id,
                currency=quote_currency
            ).first()
        else:
            # For sell orders, lock base currency
            required_amount = quantity
            wallet = Wallet.query.filter_by(
                user_id=current_user_id,
                currency=base_currency
            ).first()

        if not wallet or wallet.available_balance < required_amount:
            return jsonify({'error': 'Insufficient balance'}), 400

        # Lock the balance
        if not wallet.lock_balance(required_amount):
            return jsonify({'error': 'Failed to lock balance'}), 500

        # Create order
        order = Order(
            user_id=current_user_id,
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
            'message': 'Order placed successfully',
            'order': order.to_dict()
        }), 201

    except ValueError as e:
        return jsonify({'error': f'Invalid number format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Get user's orders"""
    try:
        current_user_id = get_jwt_identity()

        # Query parameters
        status = request.args.get('status')
        trading_pair = request.args.get('pair')
        limit = int(request.args.get('limit', 50))

        # Build query
        query = Order.query.filter_by(user_id=current_user_id)

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


@bp.route('/order/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get specific order details"""
    try:
        current_user_id = get_jwt_identity()

        order = Order.query.filter_by(
            order_id=order_id,
            user_id=current_user_id
        ).first()

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        return jsonify({'order': order.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/order/<order_id>', methods=['DELETE'])
@jwt_required()
def cancel_order(order_id):
    """Cancel an order"""
    try:
        current_user_id = get_jwt_identity()

        order = Order.query.filter_by(
            order_id=order_id,
            user_id=current_user_id
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
def get_orderbook():
    """Get order book for a trading pair"""
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
def get_recent_trades():
    """Get recent trades for a pair"""
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


@bp.route('/trades/user', methods=['GET'])
@jwt_required()
def get_user_trades():
    """Get user's trade history"""
    try:
        current_user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 50))

        # Get user's orders
        user_order_ids = [o.id for o in Order.query.filter_by(user_id=current_user_id).all()]

        # Get trades involving user's orders
        trades = Trade.query.filter(
            (Trade.maker_order_id.in_(user_order_ids)) |
            (Trade.taker_order_id.in_(user_order_ids))
        ).order_by(Trade.executed_at.desc()).limit(limit).all()

        return jsonify({
            'trades': [trade.to_dict() for trade in trades]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _get_market_price(trading_pair, side='ask'):
    """Get current market price (for market orders)"""
    orderbook = matching_engine.get_orderbook(trading_pair, depth=1)

    if side == 'ask' and orderbook['asks']:
        return Decimal(str(orderbook['asks'][0]['price']))
    elif side == 'bid' and orderbook['bids']:
        return Decimal(str(orderbook['bids'][0]['price']))

    return Decimal('0')