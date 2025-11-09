import eventlet

eventlet.monkey_patch()

import os
from app import create_app, db, socketio
from app.models.timescale_init import init_timescaledb

app = create_app(os.getenv('FLASK_ENV', 'development'))


def setup_database():
    """Setup database with proper order for TimescaleDB"""
    try:
        # First, create all tables WITHOUT unique constraints
        print("🔄 Creating database tables...")
        db.create_all()

        # Then initialize TimescaleDB hypertables
        print("🔄 Initializing TimescaleDB...")
        init_timescaledb()

        print("✅ Database setup complete!")

    except Exception as e:
        print(f"❌ Database setup error: {e}")
        raise


if __name__ == '__main__':
    with app.app_context():
        setup_database()

    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG'],
        allow_unsafe_werkzeug=True
    )