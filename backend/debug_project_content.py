from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("\n--- PROJECTS MATCHING 'test' or 'new' ---")
projects = db.execute(text("SELECT id, title, created_at FROM user_literature_reviews WHERE title ILIKE '%test%' OR title ILIKE '%new%' ORDER BY created_at DESC")).fetchall()
for p in projects:
    print(f"Project ID: {p.id} | Title: {p.title} | {p.created_at}")
    
print("\n--- SEARCHING FOR PAPERS 'GAN' or 'Attention' ---")
papers = db.execute(text("SELECT id, title FROM papers WHERE title ILIKE '%GAN%' OR title ILIKE '%Attention%'")).fetchall()
for p in papers:
    print(f"\nPaper ID: {p.id} | Title: {p.title}")
    
    # Check which projects this paper belongs to
    assignments = db.execute(text("SELECT project_id FROM project_papers WHERE paper_id = :pid"), {'pid': p.id}).fetchall()
    if assignments:
        print(f"  -> Assigned to Project IDs: {[a.project_id for a in assignments]}")
    else:
        print("  -> Assigned to NO PROJECTS")

print("\n--- ALL PROJECT ASSIGNMENTS ---")
counts = db.execute(text("SELECT project_id, COUNT(*) as count FROM project_papers GROUP BY project_id")).fetchall()
for c in counts:
    print(f"Project {c.project_id} has {c.count} papers")
