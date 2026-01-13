"""Check paper 1856 RAG status"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
r = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks WHERE metadata_->>'paper_id' = '1856'"))
print(f"RAG chunks for paper 1856: {r.fetchone()[0]}")

r = db.execute(text("SELECT COUNT(*) FROM paper_sections WHERE paper_id = 1856"))
print(f"Sections for paper 1856: {r.fetchone()[0]}")
db.close()
