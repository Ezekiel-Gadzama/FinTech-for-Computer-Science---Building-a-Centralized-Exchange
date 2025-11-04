from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
import redis

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()
redis_client = None


def create_app(config_name='default'):
    app = Flask(__name__)

    # Import config here to avoid circular imports
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(trading_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(market_bp)

    # Import models to register them with SQLAlchemy
    from .models import user, wallet, order, transaction

    # Initialize services after app is created
    with app.app_context():
        from .services.matching_engine import matching_engine
        matching_engine.start()

    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    return app