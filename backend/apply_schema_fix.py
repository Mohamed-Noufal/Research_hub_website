"""
Apply database schema fixes for AI tools
Adds missing custom_attributes column to methodology_data
"""
from app.core.database import SessionLocal
from sqlalchemy import text

def run_migrations():
    db = SessionLocal()
    try:
        # Add custom_attributes to methodology_data if missing
        db.execute(text("""
            ALTER TABLE methodology_data 
            ADD COLUMN IF NOT EXISTS custom_attributes JSONB DEFAULT '{}'
        """))
        db.commit()
        print("✅ Added custom_attributes column to methodology_data")
        
    except Exception as e:
        print(f"Migration error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migrations()
