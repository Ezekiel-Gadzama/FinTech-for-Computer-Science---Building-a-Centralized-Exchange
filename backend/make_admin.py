#!/usr/bin/env python3
"""Script to make a user an admin"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db


def make_admin(username_or_email):
    """Make a user an admin by username or email"""
    app = create_app()
    
    with app.app_context():
        # Use raw SQL to avoid ORM column issues
        # This works even if some columns don't exist in the database yet
        try:
            from sqlalchemy import text
            
            # Debug: Check database connection
            print(f"Searching for user: '{username_or_email}'")
            print(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")
            
            # First, let's see what users exist (for debugging)
            all_users = db.session.execute(
                text("SELECT id, username, email, is_admin FROM users LIMIT 10")
            ).fetchall()
            
            if all_users:
                print(f"\nFound {len(all_users)} user(s) in database:")
                for u in all_users:
                    print(f"   - ID: {u[0]}, Username: '{u[1]}', Email: '{u[2]}', Admin: {u[3]}")
            else:
                print("No users found in database")
            
            # Try case-insensitive search (PostgreSQL uses ILIKE)
            result = db.session.execute(
                text("""
                    SELECT id, username, email, is_admin 
                    FROM users 
                    WHERE LOWER(username) = LOWER(:identifier) 
                       OR LOWER(email) = LOWER(:identifier)
                    LIMIT 1
                """),
                {"identifier": username_or_email}
            ).fetchone()
            
            if not result:
                print(f"\nUser '{username_or_email}' not found")
                print("Tip: Make sure the username/email is spelled correctly (case-insensitive)")
                return False
            
            user_id, username, email, is_admin = result
            
            if is_admin:
                print(f"User '{username}' ({email}) is already an admin")
                return True
            
            # Update the user to be an admin
            db.session.execute(
                text("UPDATE users SET is_admin = TRUE WHERE id = :user_id"),
                {"user_id": user_id}
            )
            db.session.commit()
            
            print(f"Successfully made '{username}' ({email}) an admin")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            print("\n Tip: If you see a column error, you may need to run database migrations:")
            print("   flask db upgrade")
            return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <username_or_email>")
        print("Example: python make_admin.py admin@example.com")
        print("Example: python make_admin.py admin_user")
        sys.exit(1)
    
    username_or_email = sys.argv[1]
    success = make_admin(username_or_email)
    sys.exit(0 if success else 1)

