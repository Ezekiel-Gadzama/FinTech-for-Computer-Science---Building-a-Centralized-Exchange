from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Add this import
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
import redis

db = SQLAlchemy()
migrate = Migrate()  # Add this line
jwt = JWTManager()
socketio = SocketIO()
redis_client = None


def create_app(config_name='default'):
    app = Flask(__name__)

    from .config import config

    if config_name == 'testing':
        from .config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # REMOVE Flask CORS - nginx handles it
    # CORS(app, origins=app.config['CORS_ORIGINS'])

    # Socket.IO without Redis message queue for now
    socketio.init_app(app,
                      cors_allowed_origins=['http://localhost:3000'],
                      async_mode='eventlet')

    # Initialize Redis
    global redis_client
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'])
        print("Redis connected successfully")
    except Exception as e:
        redis_client = None
        print(f"Redis connection failed: {e}")

    # Import and register blueprints
    from .routes.auth import bp as auth_bp
    from .routes.trading import bp as trading_bp
    from .routes.wallet import bp as wallet_bp
    from .routes.market import bp as market_bp
    from .routes.admin import bp as admin_bp
    from .routes.kyc import bp as kyc_bp
    from .routes.api_keys import bp as api_keys_bp
    from .routes.api import bp as api_bp
    from .routes.security import bp as security_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(trading_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(kyc_bp)
    app.register_blueprint(api_keys_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(security_bp)

    # Import models to register them with SQLAlchemy
    from .models import user, wallet, order, transaction, cold_wallet, kyc, api_key

    # Initialize services after app is created
    with app.app_context():
        from .services.matching_engine import matching_engine
        # Set matching algorithm from config
        matching_algorithm = app.config.get('MATCHING_ALGORITHM', 'FIFO')
        matching_engine.matching_algorithm = matching_algorithm
        matching_engine.start()

    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    return app