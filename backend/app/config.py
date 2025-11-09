import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'

    # TimescaleDB (PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://crypto_user:crypto_pass@localhost:5432/crypto_exchange'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'connect_args': {
            'options': '-c timezone=utc'
        }
    }

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Web3
    WEB3_PROVIDER = os.getenv('WEB3_PROVIDER', 'https://mainnet.infura.io/v3/YOUR_KEY')

    # Redis (use localhost for Memurai on Windows)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # Trading
    SUPPORTED_PAIRS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
    TRADING_FEE = 0.001  # 0.1%
    MIN_ORDER_SIZE = 10  # USDT
    MATCHING_ALGORITHM = os.getenv('MATCHING_ALGORITHM', 'FIFO')  # FIFO or PRO_RATA

    # Security
    BCRYPT_LOG_ROUNDS = 12
    RATE_LIMIT = "100 per hour"

    # SocketIO
    SOCKETIO_MESSAGE_QUEUE = REDIS_URL
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS

    # TimescaleDB specific
    TIMESCALE_ENABLED = True
    
    # File uploads
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory SQLite for tests
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    REDIS_URL = 'redis://localhost:6379/1'  # Use different DB for tests

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # SocketIO config for testing
    SOCKETIO_MESSAGE_QUEUE = None


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}