"""
Comprehensive tests for API endpoints
"""
import pytest
import sys
import os
import json
from decimal import Decimal

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from app.models.wallet import Wallet
from app.models.order import Order
from flask_jwt_extended import create_access_token


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


@pytest.fixture
def test_user(app):
    """Create a test user and return auth token"""
    with app.app_context():
        user = User(email='test@test.com', username='testuser', password='test123')
        db.session.add(user)
        db.session.commit()

        # Create wallets
        usdt_wallet = Wallet(user_id=user.id, currency='USDT', balance=10000)
        btc_wallet = Wallet(user_id=user.id, currency='BTC', balance=1)
        db.session.add_all([usdt_wallet, btc_wallet])
        db.session.commit()

        token = create_access_token(identity=user.id)
        return {'user_id': user.id, 'token': token}


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers"""
    return {'Authorization': f'Bearer {test_user["token"]}'}


class TestTradingEndpoints:
    """Test trading endpoints"""

    def test_place_order(self, client, auth_headers, app, test_user):
        """Test placing an order"""
        with app.app_context():
            # Get fresh wallet instance within the current session
            wallet = Wallet.query.filter_by(user_id=test_user['user_id'], currency='USDT').first()

            # Lock balance within the same session context
            wallet.lock_balance(Decimal('5000'))
            db.session.commit()

            # Now place the order
            response = client.post('/api/trading/order',
                headers=auth_headers,
                json={
                    'trading_pair': 'BTC/USDT',
                    'side': 'buy',
                    'order_type': 'limit',
                    'quantity': '0.1',
                    'price': '50000'
                })

            # Check for successful response (200 or 201)
            assert response.status_code in [200, 201]
            if response.status_code in [200, 201]:
                data = json.loads(response.data)
                assert 'order' in data or 'order_id' in data

    def test_get_orders(self, client, auth_headers):
        """Test getting user orders"""
        response = client.get('/api/trading/orders', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'orders' in data

    def test_get_orderbook(self, client):
        """Test getting order book"""
        response = client.get('/api/trading/orderbook?pair=BTC/USDT&depth=20')

        assert response.status_code == 200
        data = json.loads(response.data)
        # Handle different response structures
        if 'orderbook' in data:
            assert 'bids' in data['orderbook']
            assert 'asks' in data['orderbook']
        else:
            assert 'bids' in data
            assert 'asks' in data

    def test_get_recent_trades(self, client):
        """Test getting recent trades"""
        response = client.get('/api/trading/trades?pair=BTC/USDT&limit=50')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'trades' in data


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_register(self, client):
        """Test user registration"""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@test.com',
            'username': 'newuser',
            'password': 'password123'
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'access_token' in data
        assert data['user']['email'] == 'newuser@test.com'

    def test_login(self, client, app):
        """Test user login"""
        with app.app_context():
            user = User(email='login@test.com', username='loginuser', password='password123')
            db.session.add(user)
            db.session.commit()

        response = client.post('/api/auth/login', json={
            'username': 'loginuser',
            'password': 'password123'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info"""
        response = client.get('/api/auth/me', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'user' in data


class TestWalletEndpoints:
    """Test wallet endpoints"""

    def test_get_balances(self, client, auth_headers):
        """Test getting wallet balances"""
        response = client.get('/api/wallet/balances', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'balances' in data

    def test_deposit(self, client, auth_headers, app, test_user):
        """Test deposit endpoint"""
        with app.app_context():
            response = client.post('/api/wallet/deposit',
                headers=auth_headers,
                json={
                    'currency': 'USDT',
                    'amount': '1000',
                    'description': 'Test deposit'
                })

            assert response.status_code in [200, 201]
            if response.status_code in [200, 201]:
                data = json.loads(response.data)
                assert 'transaction' in data or 'message' in data

    def test_withdraw(self, client, auth_headers, app, test_user):
        """Test withdrawal endpoint"""
        with app.app_context():
            # First ensure the user has balance
            wallet = Wallet.query.filter_by(user_id=test_user['user_id'], currency='USDT').first()
            if wallet:
                wallet.add_balance(Decimal('1000'))
                db.session.commit()

            response = client.post('/api/wallet/withdraw',
                headers=auth_headers,
                json={
                    'currency': 'USDT',
                    'amount': '500',
                    'address': '0x1234567890abcdef',
                    'description': 'Test withdrawal'
                })

            # Check if endpoint exists and handles the request
            assert response.status_code in [200, 201]

    def test_get_transactions(self, client, auth_headers):
        """Test getting transaction history"""
        response = client.get('/api/wallet/transactions', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'transactions' in data


class TestMarketEndpoints:
    """Test market data endpoints"""

    def test_get_prices(self, client):
        """Test getting market prices"""
        response = client.get('/api/market/prices')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'prices' in data or isinstance(data, dict)

    def test_get_ticker(self, client):
        """Test getting ticker data"""
        response = client.get('/api/market/ticker?pair=BTC/USDT')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'pair' in data or 'price' in data

    def test_get_trading_pairs(self, client):
        """Test getting trading pairs"""
        response = client.get('/api/market/pairs')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'pairs' in data or isinstance(data, list)


class TestKYCEndpoints:
    """Test KYC endpoints"""

    def test_submit_kyc(self, client, auth_headers):
        """Test submitting KYC information"""
        response = client.post('/api/auth/kyc',
            headers=auth_headers,
            json={
                'full_name': 'John Doe',
                'date_of_birth': '1990-01-01',
                'country': 'USA',
                'nationality': 'American',
                'phone': '+1234567890',
                'address': '123 Main St',
                'city': 'New York',
                'postal_code': '10001'
            })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data or 'kyc' in data

    def test_get_kyc_status(self, client, auth_headers):
        """Test getting KYC status"""
        response = client.get('/api/auth/kyc/status', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'verified' in data or 'kyc_level' in data


class TestAPIKeyEndpoints:
    """Test API key endpoints"""

    def test_create_api_key(self, client, auth_headers):
        """Test creating API key"""
        response = client.post('/api/api-keys',
            headers=auth_headers,
            json={
                'name': 'Test API Key',
                'permissions': ['read', 'trade']
            })

        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert 'api_key' in data or 'key' in data

    def test_get_api_keys(self, client, auth_headers):
        """Test getting API keys"""
        response = client.get('/api/api-keys', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'api_keys' in data or isinstance(data, list)


class TestSecurityEndpoints:
    """Test security endpoints"""

    def test_setup_2fa(self, client, auth_headers):
        """Test setting up 2FA"""
        response = client.post('/api/security/2fa/setup', headers=auth_headers)

        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert 'secret' in data or 'qr_code' in data

    def test_get_2fa_status(self, client, auth_headers):
        """Test getting 2FA status"""
        response = client.get('/api/security/2fa/status', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'enabled' in data or 'two_factor_enabled' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])