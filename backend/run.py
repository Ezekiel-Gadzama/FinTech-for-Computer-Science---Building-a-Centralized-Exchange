# run.py - ADD THIS AT THE VERY TOP
import eventlet
eventlet.monkey_patch()

import os
from app import create_app, socketio, db
from app.models.timescale_init import init_timescaledb

app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    from app.models.user import User
    from app.models.wallet import Wallet
    from app.models.order import Order, Trade
    from app.models.transaction import Transaction

    return {
        'db': db,
        'User': User,
        'Wallet': Wallet,
        'Order': Order,
        'Trade': Trade,
        'Transaction': Transaction
    }


if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created")

            # Initialize TimescaleDB hypertables
            init_timescaledb()
        except Exception as e:
            print(f"Database initialization error: {e}")

    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG'],
        allow_unsafe_werkzeug=True
    )