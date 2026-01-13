"""
Check if paper_sections has data (sections extracted by pdf_extractor)
"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check paper_sections table
try:
    r = db.execute(text("SELECT COUNT(*) FROM paper_sections"))
    print(f"paper_sections count: {r.fetchone()[0]}")
    
    r = db.execute(text("SELECT paper_id, section_type, section_title FROM paper_sections LIMIT 5"))
    for row in r.fetchall():
        print(f"  Paper {row[0]}: [{row[1]}] {row[2][:50]}...")
except Exception as e:
    print(f"paper_sections error: {e}")

# Check if data_paper_chunks exists (LlamaIndex-managed table)
print("\n--- LlamaIndex table ---")
try:
    r = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks"))
    print(f"data_paper_chunks count: {r.fetchone()[0]}")
except Exception as e:
    print(f"data_paper_chunks error: {e}")

db.close()
