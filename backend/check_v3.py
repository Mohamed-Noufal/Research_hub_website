"""
Check paper_chunks v2 - simpler
"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("SELECT COUNT(*) FROM paper_chunks"))
    print(f"paper_chunks count: {r.fetchone()[0]}")
except Exception as e:
    print(f"paper_chunks error: {e}")
    
    # Check if table even exists
    r = db.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name LIKE '%chunk%'
    """))
    print(f"Chunk tables: {[row[0] for row in r.fetchall()]}")

db.close()
