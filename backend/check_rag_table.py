"""
Check paper_chunks table (RAG engine uses this)
"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== Checking paper_chunks table ===")
r = db.execute(text("SELECT COUNT(*) FROM paper_chunks"))
print(f"Total chunks in paper_chunks: {r.fetchone()[0]}")

# Column structure
r = db.execute(text("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'paper_chunks' ORDER BY ordinal_position
"""))
print(f"Columns: {[row[0] for row in r.fetchall()]}")

# Sample data
r = db.execute(text("SELECT id, node_id FROM paper_chunks LIMIT 3"))
print(f"Sample rows:")
for row in r.fetchall():
    print(f"  id={row[0]}, node_id={row[1]}")

db.close()
