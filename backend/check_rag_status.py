"""Check RAG chunks status"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Total chunks
r = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks"))
total = r.fetchone()[0]
print(f"Total RAG chunks: {total}")

# Chunks for paper 1741
r = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks WHERE metadata_->>'paper_id' = '1741'"))
paper_chunks = r.fetchone()[0]
print(f"Chunks for paper 1741: {paper_chunks}")

# Sample metadata
if total > 0:
    r = db.execute(text("SELECT metadata_->>'paper_id', metadata_->>'section_type' FROM data_paper_chunks LIMIT 5"))
    print("\nSample chunks:")
    for row in r.fetchall():
        print(f"  Paper {row[0]}: section={row[1]}")

db.close()
