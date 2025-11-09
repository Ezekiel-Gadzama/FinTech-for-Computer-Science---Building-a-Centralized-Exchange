"""Security-related routes (2FA, etc.)"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.user import User
import pyotp
import qrcode
import io
import base64

bp = Blueprint('security', __name__, url_prefix='/api/security')


@bp.route('/2fa/setup', methods=['POST'])
@jwt_required()
def setup_2fa():
    """Setup 2FA for user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.two_factor_enabled:
            return jsonify({'error': '2FA is already enabled'}), 400
        
        # Generate TOTP secret
        secret = pyotp.random_base32()
        
        # Store secret temporarily (in production, encrypt this)
        # For now, we'll store it in a separate field or encrypt it
        user.totp_secret = secret  # Add this field to User model if needed
        
        # Generate provisioning URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name='Crypto Exchange'
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        db.session.commit()
        
        return jsonify({
            'message': '2FA setup initiated',
            'secret': secret,  # Only shown once
            'qr_code': f"data:image/png;base64,{qr_code_base64}",
            'manual_entry_key': secret
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/2fa/verify', methods=['POST'])
@jwt_required()
def verify_2fa():
    """Verify 2FA token and enable 2FA"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        token = data.get('token')
        secret = getattr(user, 'totp_secret', None)
        
        if not secret:
            return jsonify({'error': '2FA not set up'}), 400
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        # Verify token
        totp = pyotp.TOTP(secret)
        if not totp.verify(token, valid_window=1):
            return jsonify({'error': 'Invalid token'}), 400
        
        # Enable 2FA
        user.two_factor_enabled = True
        db.session.commit()
        
        return jsonify({
            'message': '2FA enabled successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/2fa/disable', methods=['POST'])
@jwt_required()
def disable_2fa():
    """Disable 2FA"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        password = data.get('password')
        token = data.get('token')
        
        # Verify password
        if not user.check_password(password):
            return jsonify({'error': 'Invalid password'}), 401
        
        # Verify 2FA token if enabled
        if user.two_factor_enabled:
            secret = getattr(user, 'totp_secret', None)
            if secret and token:
                totp = pyotp.TOTP(secret)
                if not totp.verify(token, valid_window=1):
                    return jsonify({'error': 'Invalid 2FA token'}), 401
        
        # Disable 2FA
        user.two_factor_enabled = False
        user.totp_secret = None
        db.session.commit()
        
        return jsonify({
            'message': '2FA disabled successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/2fa/status', methods=['GET'])
@jwt_required()
def get_2fa_status():
    """Get 2FA status"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'two_factor_enabled': user.two_factor_enabled
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

