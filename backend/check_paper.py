"""
Check if paper has been processed
"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Get paper in project 43
r = db.execute(text("""
    SELECT p.id, p.title, p.is_processed, p.source_url, p.pdf_path
    FROM papers p 
    JOIN project_papers pp ON pp.paper_id = p.id 
    WHERE pp.project_id = 43
    LIMIT 5
"""))
print("Papers in project 43:")
for row in r.fetchall():
    print(f"  ID: {row[0]}")
    print(f"  Title: {row[1][:50]}...")
    print(f"  is_processed: {row[2]}")
    print(f"  source_url: {row[3]}")
    print(f"  pdf_path: {row[4]}")

# Check if any chunks exist with matching paper_id
print("\nChunks check:")
r = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks"))
total = r.fetchone()[0]
print(f"Total chunks in data_paper_chunks: {total}")

# Sample metadata from chunks
if total > 0:
    r = db.execute(text("SELECT metadata FROM data_paper_chunks LIMIT 3"))
    print("\nSample chunk metadata:")
    for row in r.fetchall():
        print(f"  {row[0]}")

db.close()
