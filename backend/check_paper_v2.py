"""
Check papers and chunks - v2
"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("Papers in project 43:")
r = db.execute(text("SELECT p.id, p.title FROM papers p JOIN project_papers pp ON pp.paper_id = p.id WHERE pp.project_id = 43 LIMIT 5"))
for row in r.fetchall():
    print(f"  ID: {row[0]}, Title: {row[1][:40]}...")

print("\nTotal chunks:")
r = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks"))
print(f"  {r.fetchone()[0]}")

print("\nSample chunk metadata:")
r = db.execute(text("SELECT node_id, metadata FROM data_paper_chunks LIMIT 2"))
for row in r.fetchall():
    print(f"  node_id: {row[0]}")
    print(f"  metadata: {row[1]}")

db.close()
