"""KYC document upload and management routes"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from .. import db
from ..models.kyc import KYCDocument, KYCVerification
from ..utils.decorators import admin_required
from datetime import datetime, timedelta
import os
import uuid

bp = Blueprint('kyc', __name__, url_prefix='/api/kyc')

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    """Upload KYC document"""
    try:
        current_user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        document_type = request.form.get('document_type')
        
        if not document_type:
            return jsonify({'error': 'Document type required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large (max 10MB)'}), 400
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'kyc')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        secure_name = f"{current_user_id}_{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, secure_name)
        
        # Save file
        file.save(file_path)
        
        # Create document record
        document = KYCDocument(
            user_id=current_user_id,
            document_type=document_type,
            file_path=file_path,
            file_name=file.filename,
            file_size=file_size,
            mime_type=file.content_type,
            expires_at=datetime.utcnow() + timedelta(days=365)  # Documents expire after 1 year
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            'message': 'Document uploaded successfully',
            'document': document.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/documents', methods=['GET'])
@jwt_required()
def get_documents():
    """Get user's KYC documents"""
    try:
        current_user_id = get_jwt_identity()
        
        documents = KYCDocument.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/verify/<user_id>', methods=['POST'])
@jwt_required()
@admin_required
def verify_kyc(user_id):
    """Verify user's KYC (admin only)"""
    try:
        verifier_id = get_jwt_identity()
        data = request.get_json()
        
        kyc_verification = KYCVerification.query.filter_by(user_id=user_id).first()
        if not kyc_verification:
            return jsonify({'error': 'KYC not found'}), 404
        
        # Check documents
        documents = KYCDocument.query.filter_by(user_id=user_id, status='pending').all()
        if not documents:
            return jsonify({'error': 'No pending documents to verify'}), 400
        
        # Update verification
        kyc_verification.verified = True
        kyc_verification.verified_by = verifier_id
        kyc_verification.verified_at = datetime.utcnow()
        kyc_verification.verification_notes = data.get('notes', '')
        kyc_verification.aml_status = data.get('aml_status', 'cleared')
        kyc_verification.risk_score = data.get('risk_score', 0)
        
        # Update user
        from ..models.user import User
        user = User.query.get(user_id)
        if user:
            user.kyc_verified = True
            user.kyc_level = kyc_verification.kyc_level
        
        # Update documents
        for doc in documents:
            doc.status = 'verified'
            doc.verified_by = verifier_id
            doc.verified_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'KYC verified successfully',
            'kyc': kyc_verification.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/reject/<user_id>', methods=['POST'])
@jwt_required()
@admin_required
def reject_kyc(user_id):
    """Reject user's KYC (admin only)"""
    try:
        verifier_id = get_jwt_identity()
        data = request.get_json()
        
        kyc_verification = KYCVerification.query.filter_by(user_id=user_id).first()
        if not kyc_verification:
            return jsonify({'error': 'KYC not found'}), 404
        
        # Update verification
        kyc_verification.verified = False
        kyc_verification.verified_by = verifier_id
        kyc_verification.verification_notes = data.get('reason', 'KYC rejected')
        kyc_verification.aml_status = 'blocked'
        
        # Update documents
        documents = KYCDocument.query.filter_by(user_id=user_id).all()
        for doc in documents:
            doc.status = 'rejected'
            doc.verified_by = verifier_id
            doc.verification_notes = data.get('reason', '')
        
        db.session.commit()
        
        return jsonify({
            'message': 'KYC rejected',
            'kyc': kyc_verification.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/pending', methods=['GET'])
@jwt_required()
@admin_required
def get_pending_kyc():
    """Get all pending KYC verifications (admin only)"""
    try:
        verifications = KYCVerification.query.filter_by(verified=False).all()
        
        return jsonify({
            'pending_kyc': [v.to_dict(include_sensitive=True) for v in verifications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/documents/<user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user_documents(user_id):
    """Get KYC documents for a specific user (admin only)"""
    try:
        documents = KYCDocument.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
