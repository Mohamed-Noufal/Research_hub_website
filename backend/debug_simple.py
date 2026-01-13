"""
Simple debug script
"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Simple check
r = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks"))
print(f"Total chunks: {r.fetchone()[0]}")

# Check papers
r = db.execute(text("SELECT id, title FROM papers LIMIT 5"))
for row in r.fetchall():
    print(f"Paper {row[0]}: {row[1][:40]}")

# Check methodology data for project 43
r = db.execute(text("SELECT paper_id, methodology_description FROM methodology_data WHERE project_id = '43' LIMIT 5"))
print("\nMethodology data:")
for row in r.fetchall():
    print(f"  Paper {row[0]}: '{row[1]}'")

db.close()
