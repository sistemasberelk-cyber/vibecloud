from sqlmodel import Session
from sqlalchemy import text
from database.session import engine

try:
    with Session(engine) as session:
        session.exec(text("ALTER TABLE settings ADD COLUMN IF NOT EXISTS is_onboarded BOOLEAN DEFAULT FALSE"))
        session.exec(text("ALTER TABLE settings ADD COLUMN IF NOT EXISTS onboarding_step INTEGER DEFAULT 1"))
        # Any other missing columns? Let's also add SyncQueue just in case!
        session.exec(text("""
            CREATE TABLE IF NOT EXISTS syncqueue (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL,
                entity_type VARCHAR NOT NULL,
                entity_id VARCHAR NOT NULL,
                action VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                payload JSON,
                error_message VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """))
        session.commit()
        print("Database schema fixed successfully!")
except Exception as e:
    print(f"Failed: {e}")
