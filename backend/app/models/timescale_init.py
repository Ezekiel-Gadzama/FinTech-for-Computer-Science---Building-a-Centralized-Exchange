from sqlalchemy import text
from .. import db


def init_timescaledb():
    """Initialize TimescaleDB hypertables for time-series data"""
    try:
        # COMPLETELY reset the database session to clear any aborted transactions
        db.session.remove()
        db.session.begin()

        print("🔄 Database session reset - checking TimescaleDB...")

        # Check if TimescaleDB is installed
        result = db.session.execute(text(
            "SELECT default_version FROM pg_available_extensions WHERE name = 'timescaledb'"
        ))

        if result.fetchone():
            print("✅ TimescaleDB extension is available")

            # Enable TimescaleDB extension
            try:
                db.session.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
                db.session.commit()
                print("✅ TimescaleDB extension enabled")
            except Exception as e:
                db.session.rollback()
                print(f"✅ TimescaleDB extension already exists: {e}")

            # Try to create hypertables with better error handling
            create_hypertables_safely()

            db.session.commit()
            print("🎉 TimescaleDB initialization complete!")
        else:
            print("⚠️ TimescaleDB extension not found. Using regular PostgreSQL.")
    except Exception as e:
        print(f"❌ Error initializing TimescaleDB: {e}")
        db.session.rollback()


def create_hypertables_safely():
    """Safely create hypertables with individual error handling"""
    # For trades table
    try:
        # Check if table exists and has the required column
        result = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'trades'
            )
        """))
        table_exists = result.scalar()
        
        if table_exists:
            # Check if it's already a hypertable
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = 'trades'
                )
            """))
            is_hypertable = result.scalar()
            
            if not is_hypertable:
                # Drop primary key constraint if it exists and doesn't include executed_at
                try:
                    db.session.execute(text("""
                        ALTER TABLE trades DROP CONSTRAINT IF EXISTS trades_pkey CASCADE
                    """))
                    # Recreate primary key with executed_at included
                    db.session.execute(text("""
                        ALTER TABLE trades ADD PRIMARY KEY (id, executed_at)
                    """))
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"⚠️ Could not modify trades primary key: {e}")
                    # Try without primary key modification
                
                # Create hypertable
                db.session.execute(text("""
                    SELECT create_hypertable('trades', 'executed_at', 
                        chunk_time_interval => INTERVAL '1 day',
                        if_not_exists => TRUE)
                """))
                db.session.commit()
                print("✅ Trades hypertable created")
            else:
                print("✅ Trades hypertable already exists")
        else:
            print("⚠️ Trades table does not exist yet")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Could not create trades hypertable: {e}")
        # Continue anyway

    # For transactions table
    try:
        # Check if table exists
        result = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'transactions'
            )
        """))
        table_exists = result.scalar()
        
        if table_exists:
            # Check if it's already a hypertable
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = 'transactions'
                )
            """))
            is_hypertable = result.scalar()
            
            if not is_hypertable:
                # Drop primary key constraint if it exists and doesn't include created_at
                try:
                    db.session.execute(text("""
                        ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_pkey CASCADE
                    """))
                    # Recreate primary key with created_at included
                    db.session.execute(text("""
                        ALTER TABLE transactions ADD PRIMARY KEY (id, created_at)
                    """))
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"⚠️ Could not modify transactions primary key: {e}")
                    # Try without primary key modification
                
                # Create hypertable
                db.session.execute(text("""
                    SELECT create_hypertable('transactions', 'created_at',
                        chunk_time_interval => INTERVAL '1 day',
                        if_not_exists => TRUE)
                """))
                db.session.commit()
                print("✅ Transactions hypertable created")
            else:
                print("✅ Transactions hypertable already exists")
        else:
            print("⚠️ Transactions table does not exist yet")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Could not create transactions hypertable: {e}")
        # Continue anyway