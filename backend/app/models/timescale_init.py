from sqlalchemy import text
from .. import db

def init_timescaledb():
    """Initialize TimescaleDB hypertables for time-series data"""
    try:
        # Check if TimescaleDB is installed
        result = db.session.execute(text(
            "SELECT default_version FROM pg_available_extensions WHERE name = 'timescaledb'"
        ))

        if result.fetchone():
            print("TimescaleDB extension is available")

            # Fixed syntax for create_hypertable
            try:
                # Check if trades is already a hypertable
                check_query = text("""
                    SELECT * FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = 'trades'
                """)
                result = db.session.execute(check_query)

                if not result.fetchone():
                    db.session.execute(text(
                        "SELECT create_hypertable('trades', 'executed_at')"
                    ))
                    print("Created hypertable for trades")
                else:
                    print("Hypertable for trades already exists")
            except Exception as e:
                print(f"Hypertable for trades: {e}")

            # Same for transactions
            try:
                check_query = text("""
                    SELECT * FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = 'transactions'
                """)
                result = db.session.execute(check_query)

                if not result.fetchone():
                    db.session.execute(text(
                        "SELECT create_hypertable('transactions', 'created_at')"
                    ))
                    print("Created hypertable for transactions")
                else:
                    print("Hypertable for transactions already exists")
            except Exception as e:
                print(f"Hypertable for transactions: {e}")

            db.session.commit()
            print("TimescaleDB initialization complete!")
        else:
            print("Warning: TimescaleDB extension not found. Using regular PostgreSQL.")
    except Exception as e:
        print(f"Error initializing TimescaleDB: {e}")
        db.session.rollback()