import sys
import os
from sqlalchemy import text

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.core.database import engine

def run_migration():
    print("🚀 Starting migration...")
    
    try:
        # Read migration file
        with open('migrations/add_literature_review_columns.sql', 'r') as f:
            sql_content = f.read()
            
        # Execute migration
        with engine.connect() as connection:
            # Split by semicolon to handle multiple statements if needed, 
            # but SQLAlchemy text() might handle it or we might need to execute separately.
            # For safety, let's execute the whole block if possible, or split.
            # The SQL file has multiple statements.
            
            # Simple split by semicolon might be fragile if semicolons are in strings, 
            # but for this specific SQL file it should be fine.
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for statement in statements:
                print(f"Executing: {statement[:50]}...")
                connection.execute(text(statement))
                
            connection.commit()
            
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
