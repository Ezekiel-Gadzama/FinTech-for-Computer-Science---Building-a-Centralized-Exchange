"""KYC/AML models for compliance"""
from datetime import datetime
from .. import db
import uuid


class KYCDocument(db.Model):
    """KYC document uploads"""
    __tablename__ = 'kyc_documents'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Document details
    document_type = db.Column(db.String(50), nullable=False)  # passport, id_card, driver_license, proof_of_address
    file_path = db.Column(db.String(500))  # Path to stored document
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))
    
    # Verification
    status = db.Column(db.String(20), default='pending')  # pending, verified, rejected, expired
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who verified
    verification_notes = db.Column(db.Text)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    verified_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)  # Documents expire after certain period
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'document_type': self.document_type,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'status': self.status,
            'uploaded_at': self.uploaded_at.isoformat(),
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    def __repr__(self):
        return f'<KYCDocument {self.document_type} status={self.status}>'


class KYCVerification(db.Model):
    """KYC verification records"""
    __tablename__ = 'kyc_verifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)
    
    # Verification levels
    kyc_level = db.Column(db.Integer, default=0)  # 0: unverified, 1: basic, 2: advanced
    aml_status = db.Column(db.String(20), default='pending')  # pending, cleared, flagged, blocked
    
    # Personal information
    full_name = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    country = db.Column(db.String(80))
    nationality = db.Column(db.String(80))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    
    # Compliance
    pep_status = db.Column(db.Boolean, default=False)  # Politically Exposed Person
    sanctions_check = db.Column(db.Boolean, default=False)
    risk_score = db.Column(db.Integer, default=0)  # 0-100 risk score
    
    # Verification
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verification_notes = db.Column(db.Text)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    last_reviewed_at = db.Column(db.DateTime)
    
    # Relationships will be defined after both classes are declared
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'kyc_level': self.kyc_level,
            'aml_status': self.aml_status,
            'verified': self.verified,
            'risk_score': self.risk_score,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None
        }
        
        if include_sensitive:
            data.update({
                'full_name': self.full_name,
                'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
                'country': self.country,
                'nationality': self.nationality,
                'address': self.address,
                'city': self.city,
                'postal_code': self.postal_code,
                'phone': self.phone,
                'pep_status': self.pep_status,
                'sanctions_check': self.sanctions_check
            })
        
        return data

    def __repr__(self):
        return f'<KYCVerification user={self.user_id} level={self.kyc_level} verified={self.verified}>'


# Define relationship after both classes are declared
# This links KYCVerification to KYCDocument through user_id
KYCVerification.documents = db.relationship(
    KYCDocument,
    primaryjoin=KYCVerification.user_id == KYCDocument.user_id,
    foreign_keys=[KYCDocument.user_id],
    lazy='dynamic',
    viewonly=True
)

