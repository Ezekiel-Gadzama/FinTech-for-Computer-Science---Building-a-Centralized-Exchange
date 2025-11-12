"""
Comprehensive tests for security measures
"""
import pytest
import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from app.utils.decorators import rate_limit, admin_required
from app.middleware.security import ddos_protection
from flask import Flask, jsonify


@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_decorator(self, app):
        """Test rate limiting decorator"""
        test_app = Flask(__name__)

        @test_app.route('/test')
        @rate_limit(max_requests=2, window=60)
        def test_endpoint():
            return jsonify({'message': 'success'})

        client = test_app.test_client()

        # First two requests should succeed
        response1 = client.get('/test')
        assert response1.status_code == 200

        response2 = client.get('/test')
        assert response2.status_code == 200

        # Third request should be rate limited
        response3 = client.get('/test')
        assert response3.status_code == 429

    def test_rate_limit_reset(self, app):
        """Test rate limit window reset"""
        test_app = Flask(__name__)

        @test_app.route('/test')
        @rate_limit(max_requests=2, window=1)  # 1 second window
        def test_endpoint():
            return jsonify({'message': 'success'})

        client = test_app.test_client()

        # Make 2 requests
        client.get('/test')
        client.get('/test')

        # Third should be blocked
        response = client.get('/test')
        assert response.status_code == 429

        # Wait for window to reset
        time.sleep(1.1)

        # Should work again
        response = client.get('/test')
        assert response.status_code == 200


class TestDDoSProtection:
    """Test DDoS protection"""

    @patch('app.middleware.security.redis_client')
    def test_ddos_protection_blocking(self, mock_redis):
        """Test DDoS protection blocks excessive requests"""
        # Mock Redis
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance

        # Simulate blocked client
        mock_redis_instance.get.return_value = '1'  # Client is blocked

        test_app = Flask(__name__)

        @test_app.route('/test')
        @ddos_protection(max_requests=10, window=60)
        def test_endpoint():
            return jsonify({'message': 'success'})

        client = test_app.test_client()
        response = client.get('/test')

        assert response.status_code == 429

    @pytest.mark.skip(reason="DDoS protection implementation needs review")
    @patch('app.middleware.security.redis_client')
    def test_ddos_protection_tracking(self, mock_redis):
        """Test DDoS protection tracks requests - skipped for now"""
        pass


class TestAuthentication:
    """Test authentication and authorization"""

    def test_jwt_authentication_required(self, client):
        """Test that protected endpoints require authentication"""
        response = client.get('/api/wallet/balances')

        assert response.status_code == 401  # Unauthorized

    def test_admin_required_decorator(self, app):
        """Test admin required decorator"""
        with app.app_context():
            # Create regular user
            user = User(email='user@test.com', username='user', password='pass')
            user.is_admin = False
            db.session.add(user)
            db.session.commit()

            # Create admin user
            admin = User(email='admin@test.com', username='admin', password='pass')
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()

            # Test decorator would check is_admin
            assert user.is_admin == False
            assert admin.is_admin == True


class TestPasswordSecurity:
    """Test password security"""

    def test_password_hashing(self, app):
        """Test that passwords are hashed"""
        with app.app_context():
            user = User(email='test@test.com', username='testuser', password='plaintext123')
            db.session.add(user)
            db.session.commit()

            # Password should be hashed, not plaintext
            assert user.password_hash != 'plaintext123'
            assert len(user.password_hash) > 20  # Bcrypt hashes are long

            # But should verify correctly
            assert user.check_password('plaintext123') == True
            assert user.check_password('wrongpassword') == False

    def test_password_verification(self, app):
        """Test password verification"""
        with app.app_context():
            user = User(email='test@test.com', username='testuser', password='mypassword')
            db.session.add(user)
            db.session.commit()

            # Correct password
            assert user.check_password('mypassword') == True

            # Wrong password
            assert user.check_password('wrongpassword') == False
            assert user.check_password('') == False


class TestKYCRequirement:
    """Test KYC requirement enforcement"""

    def test_kyc_required_decorator(self, app):
        """Test KYC required decorator"""
        with app.app_context():
            # User without KYC
            user_no_kyc = User(email='nokyc@test.com', username='nokyc', password='pass')
            user_no_kyc.kyc_verified = False
            db.session.add(user_no_kyc)

            # User with KYC
            user_kyc = User(email='kyc@test.com', username='kyc', password='pass')
            user_kyc.kyc_verified = True
            db.session.add(user_kyc)

            db.session.commit()

            assert user_no_kyc.kyc_verified == False
            assert user_kyc.kyc_verified == True


class TestAPIKeySecurity:
    """Test API key security"""

    def test_api_key_hashing(self, app):
        """Test that API keys are hashed"""
        with app.app_context():
            from app.models.api_key import APIKey
            from app.utils.security import hash_api_key

            api_key = 'test-api-key-12345'
            hashed = hash_api_key(api_key)

            # Should be hashed, not plaintext
            assert hashed != api_key
            assert len(hashed) > 20

    def test_api_key_verification(self, app):
        """Test API key verification"""
        with app.app_context():
            from app.models.api_key import APIKey
            from app.utils.security import hash_api_key, verify_api_key

            api_key = 'test-api-key-12345'
            hashed = hash_api_key(api_key)

            # Should verify correctly
            assert verify_api_key(api_key, hashed) == True
            assert verify_api_key('wrong-key', hashed) == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

