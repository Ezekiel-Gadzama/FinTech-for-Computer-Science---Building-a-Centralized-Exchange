import pytest
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from app.models.wallet import Wallet


@pytest.fixture(scope='session')
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
def auth_headers(client):
    """Get authentication headers for tests"""
    # Create a test user and get token
    user = User(email='test@test.com', username='testuser', password='testpass')
    db.session.add(user)
    db.session.commit()

    # Login and get token (you'd need to implement this based on your auth system)
    # response = client.post('/api/auth/login', json={
    #     'username': 'testuser',
    #     'password': 'testpass'
    # })
    # token = response.json['access_token']
    # return {'Authorization': f'Bearer {token}'}

    return {}  # Placeholder