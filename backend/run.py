from app import create_app, db, socketio
from app.models.timescale_init import init_timescaledb
import os

app = create_app(os.getenv("FLASK_ENV", "development"))

def setup_database():
    print("Creating tables...")
    db.create_all()
    print("Init TimescaleDB...")
    init_timescaledb()
    print("Done.")

if __name__ == "__main__":
    with app.app_context():
        setup_database()

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        allow_unsafe_werkzeug=True
    )
