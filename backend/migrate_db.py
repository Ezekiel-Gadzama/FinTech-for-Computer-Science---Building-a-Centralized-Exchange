"""
Database migration script
Run this to initialize migrations and create/apply migrations
"""
import os
from app import create_app, db
from flask_migrate import init, migrate, upgrade

app = create_app()

with app.app_context():
    # Check if migrations directory exists
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    
    if not os.path.exists(migrations_dir):
        print("Initializing migrations...")
        init()
        print("✅ Migrations initialized")
    
    print("Creating migration...")
    migrate(message="Add new models and columns (KYC, API keys, 2FA, cold wallets)")
    print("✅ Migration created")
    
    print("Applying migration...")
    upgrade()
    print("✅ Migration applied successfully!")

