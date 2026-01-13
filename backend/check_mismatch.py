"""
Verify paper ID mismatch
"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("== Papers in Project 43 ==")
r = db.execute(text("""
    SELECT p.id, p.title 
    FROM papers p 
    JOIN project_papers pp ON pp.paper_id = p.id 
    WHERE pp.project_id = 43
"""))
for row in r.fetchall():
    print(f"  Paper ID: {row[0]}, Title: {row[1][:50]}...")

print("\n== Papers with sections in paper_sections ==")
r = db.execute(text("SELECT DISTINCT paper_id FROM paper_sections"))
for row in r.fetchall():
    print(f"  Paper ID: {row[0]}")

print("\n== Check if paper 1741 (from project 43) has any chunks ==")
r = db.execute(text("SELECT COUNT(*) FROM paper_sections WHERE paper_id = 1741"))
print(f"  paper_sections count for 1741: {r.fetchone()[0]}")

# Check LlamaIndex chunks for paper 1741
r = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks WHERE metadata_->>'paper_id' = '1741'"))
print(f"  data_paper_chunks count for 1741: {r.fetchone()[0]}")

db.close()
