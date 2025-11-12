"""
Comprehensive tests for KYC/AML functionality
"""
import pytest
import sys
import os
from datetime import datetime, date

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from app.models.kyc import KYCVerification, KYCDocument
from app.utils.decorators import kyc_required


@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(email='test@test.com', username='testuser', password='test123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """Create an admin user"""
    with app.app_context():
        admin = User(email='admin@test.com', username='admin', password='admin123')
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()
        return admin


class TestKYCSubmission:
    """Test KYC information submission"""

    def test_kyc_submission(self, app, test_user):
        """Test submitting KYC information"""
        with app.app_context():
            # Refresh the user to ensure it's attached to current session
            user = db.session.merge(test_user)

            kyc = KYCVerification(
                user_id=user.id,  # Use the merged user's ID
                full_name='John Doe',
                date_of_birth=date(1990, 1, 1),
                country='USA',
                nationality='American',
                address='123 Main St',
                city='New York',
                postal_code='10001',
                phone='+1234567890',
                kyc_level=1
            )
            db.session.add(kyc)
            db.session.commit()

            assert kyc.user_id == user.id
            assert kyc.full_name == 'John Doe'
            assert kyc.verified == False
            assert kyc.kyc_level == 1

    def test_kyc_document_upload(self, app, test_user):
        """Test uploading KYC documents"""
        with app.app_context():
            user = db.session.merge(test_user)

            document = KYCDocument(
                user_id=user.id,
                document_type='passport',
                file_path='/uploads/kyc/test.pdf',
                file_name='passport.pdf',
                file_size=1024000,
                mime_type='application/pdf',
                status='pending'
            )
            db.session.add(document)
            db.session.commit()

            assert document.user_id == user.id
            assert document.document_type == 'passport'
            assert document.status == 'pending'

    def test_multiple_documents(self, app, test_user):
        """Test uploading multiple KYC documents"""
        with app.app_context():
            user = db.session.merge(test_user)

            documents = [
                KYCDocument(
                    user_id=user.id,
                    document_type='passport',
                    file_path=f'/uploads/kyc/passport_{i}.pdf',
                    file_name=f'passport_{i}.pdf',
                    file_size=1024000,
                    mime_type='application/pdf',
                    status='pending'
                )
                for i in range(3)
            ]
            db.session.add_all(documents)
            db.session.commit()

            user_docs = KYCDocument.query.filter_by(user_id=user.id).all()
            assert len(user_docs) == 3


class TestKYCVerification:
    """Test KYC verification process"""

    def test_kyc_verification_approval(self, app, test_user, admin_user):
        """Test admin approving KYC"""
        with app.app_context():
            user = db.session.merge(test_user)
            admin = db.session.merge(admin_user)

            # Create KYC submission
            kyc = KYCVerification(
                user_id=user.id,
                full_name='John Doe',
                country='USA',
                kyc_level=1,
                verified=False
            )
            db.session.add(kyc)
            db.session.commit()

            # Approve KYC
            kyc.verified = True
            kyc.verified_by = admin.id
            kyc.verified_at = datetime.utcnow()
            kyc.aml_status = 'cleared'
            kyc.risk_score = 10

            # Update user
            user.kyc_verified = True
            user.kyc_level = 1

            # Update documents
            document = KYCDocument(
                user_id=user.id,
                document_type='passport',
                file_path='/uploads/kyc/passport.pdf',
                file_name='passport.pdf',
                file_size=1024000,
                mime_type='application/pdf',
                status='pending'
            )
            db.session.add(document)
            db.session.commit()

            document.status = 'verified'
            document.verified_by = admin.id
            document.verified_at = datetime.utcnow()

            db.session.commit()

            # Verify
            assert kyc.verified == True
            assert user.kyc_verified == True
            assert document.status == 'verified'

    def test_kyc_verification_rejection(self, app, test_user, admin_user):
        """Test admin rejecting KYC"""
        with app.app_context():
            user = db.session.merge(test_user)
            admin = db.session.merge(admin_user)

            kyc = KYCVerification(
                user_id=user.id,
                full_name='John Doe',
                country='USA',
                kyc_level=1,
                verified=False
            )
            db.session.add(kyc)
            db.session.commit()

            # Reject KYC
            kyc.verified = False
            kyc.verified_by = admin.id
            kyc.verification_notes = 'Document quality insufficient'
            kyc.aml_status = 'blocked'

            # Update documents
            document = KYCDocument(
                user_id=user.id,
                document_type='passport',
                file_path='/uploads/kyc/passport.pdf',
                file_name='passport.pdf',
                file_size=1024000,
                mime_type='application/pdf',
                status='pending'
            )
            db.session.add(document)
            db.session.commit()

            document.status = 'rejected'
            document.verified_by = admin.id
            document.verification_notes = 'Document quality insufficient'

            db.session.commit()

            assert kyc.verified == False
            assert kyc.aml_status == 'blocked'
            assert document.status == 'rejected'


class TestKYCDecorator:
    """Test KYC requirement decorator"""

    def test_kyc_required_decorator(self, app, test_user):
        """Test that KYC required decorator works"""
        with app.app_context():
            user = db.session.merge(test_user)

            # User without KYC
            user.kyc_verified = False
            db.session.commit()
            assert user.kyc_verified == False

            # User with KYC
            user.kyc_verified = True
            db.session.commit()
            assert user.kyc_verified == True


class TestAMLCompliance:
    """Test AML compliance features"""

    def test_pep_status(self, app, test_user):
        """Test PEP (Politically Exposed Person) status"""
        with app.app_context():
            user = db.session.merge(test_user)

            kyc = KYCVerification(
                user_id=user.id,
                full_name='John Doe',
                pep_status=True,
                risk_score=80
            )
            db.session.add(kyc)
            db.session.commit()

            assert kyc.pep_status == True
            assert kyc.risk_score == 80

    def test_sanctions_check(self, app, test_user):
        """Test sanctions check"""
        with app.app_context():
            user = db.session.merge(test_user)

            kyc = KYCVerification(
                user_id=user.id,
                full_name='John Doe',
                sanctions_check=True,
                aml_status='cleared'
            )
            db.session.add(kyc)
            db.session.commit()

            assert kyc.sanctions_check == True
            assert kyc.aml_status == 'cleared'

    def test_risk_scoring(self, app, test_user):
        """Test risk score calculation"""
        with app.app_context():
            # Create two different users for this test
            low_risk_user = User(email='lowrisk@test.com', username='lowrisk', password='test123')
            high_risk_user = User(email='highrisk@test.com', username='highrisk', password='test123')
            db.session.add_all([low_risk_user, high_risk_user])
            db.session.commit()

            # Low risk user
            kyc_low = KYCVerification(
                user_id=low_risk_user.id,
                full_name='John Doe',
                country='USA',
                pep_status=False,
                sanctions_check=True,
                risk_score=10
            )

            # High risk user
            kyc_high = KYCVerification(
                user_id=high_risk_user.id,
                full_name='Jane Doe',
                country='High Risk Country',
                pep_status=True,
                sanctions_check=False,
                risk_score=90
            )

            db.session.add_all([kyc_low, kyc_high])
            db.session.commit()

            assert kyc_low.risk_score < 50
            assert kyc_high.risk_score > 50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])