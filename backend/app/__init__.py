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

# IMPORTANT: Allow all CORS from React
socketio = SocketIO(cors_allowed_origins="*")

redis_client = None

def create_app(config_name='default'):
    app = Flask(__name__)

    from .config import config
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # ⭐ ENABLE FLASK CORS (since NGINX is removed)
    CORS(
        app,
        resources={r"/api/*": {"origins": "http://localhost:3000"}},
        supports_credentials=True,
    )

    # ⭐ Socket.IO CORS
    socketio.init_app(
        app,
        async_mode="threading",
        cors_allowed_origins="*"
    )

    # Redis
    global redis_client
    try:
        redis_client = redis.from_url(app.config["REDIS_URL"])
        print("Connected to Redis")
    except:
        print("Redis connection failed")
        redis_client = None

    # Register blueprints
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

    @app.route('/health')
    def health():
        return {"status": "OK"}, 200

    return app
