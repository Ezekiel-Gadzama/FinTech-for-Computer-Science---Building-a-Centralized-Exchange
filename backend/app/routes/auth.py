from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
from .. import db
from ..models.user import User
from ..models.wallet import Wallet

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()

        # Validate required fields
        if not all(k in data for k in ['email', 'username', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already taken'}), 409

        # Create new user
        user = User(
            email=data['email'],
            username=data['username'],
            password=data['password']
        )

        db.session.add(user)
        db.session.flush()  # Get user ID

        # Create initial wallets for supported currencies
        currencies = ['USDT', 'BTC', 'ETH', 'BNB', 'ADA', 'SOL']
        for currency in currencies:
            wallet = Wallet(user_id=user.id, currency=currency)
            db.session.add(wallet)

        db.session.commit()

        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()

        if not all(k in data for k in ['username', 'password']):
            return jsonify({'error': 'Missing username or password'}), 400

        # Find user
        user = User.query.filter_by(username=data['username']).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)

        return jsonify({'access_token': access_token}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': user.to_dict(include_sensitive=True)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/kyc', methods=['POST'])
@jwt_required()
def submit_kyc():
    """Submit KYC information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        # Update KYC info
        user.full_name = data.get('full_name')
        user.country = data.get('country')
        user.phone = data.get('phone')
        user.kyc_level = 1  # Basic verification
        user.kyc_verified = True

        db.session.commit()

        return jsonify({
            'message': 'KYC submitted successfully',
            'user': user.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500