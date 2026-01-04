"""
Fix Database Schema - Add missing columns
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.core.database import SessionLocal

def main():
    print("=" * 60)
    print("FIXING DATABASE SCHEMA")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Add missing columns to papers table
        migrations = [
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending'",
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0",
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS error_message TEXT",
        ]
        
        for sql in migrations:
            try:
                print(f"Running: {sql[:50]}...")
                db.execute(text(sql))
                db.commit()
                print("  ✅ Success")
            except Exception as e:
                print(f"  ⚠️ {e}")
                db.rollback()
        
        # Verify columns exist
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'papers' 
            AND column_name IN ('processing_status', 'chunk_count', 'error_message')
        """)).fetchall()
        
        print(f"\n✅ Verified columns exist: {[r[0] for r in result]}")
        
        # Check papers count
        count = db.execute(text("SELECT COUNT(*) FROM papers")).fetchone()[0]
        print(f"Papers in database: {count}")
        
    finally:
        db.close()
    
    print("\n✅ Schema fix complete!")

if __name__ == "__main__":
    main()
