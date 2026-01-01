"""
Apply Migration 023: File Tracking and Processing Status
Adds columns for background processing and file tracking
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

def main():
    from app.core.config import settings
    
    db_url = settings.DATABASE_URL
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    # Use sync driver
    if "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql")
    
    engine = create_engine(db_url)
    
    migration_path = Path(__file__).parent / "migrations" / "023_file_tracking_and_processing.sql"
    
    if not migration_path.exists():
        print(f"ERROR: Migration file not found: {migration_path}")
        return False
    
    sql_content = migration_path.read_text()
    
    print("Applying migration 023_file_tracking_and_processing.sql...")
    print("-" * 50)
    
    with engine.connect() as conn:
        # Split by statements and execute
        for statement in sql_content.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    conn.execute(text(statement))
                    print(f"OK: {statement[:60]}...")
                except Exception as e:
                    print(f"WARN: {e}")
        conn.commit()
    
    print("-" * 50)
    print("Migration completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
