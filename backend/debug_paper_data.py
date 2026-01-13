"""
Debug script to check paper chunks and RAG data
"""
from app.core.database import SessionLocal
from sqlalchemy import text

def debug_paper_data():
    db = SessionLocal()
    try:
        # Check paper chunks table
        print("\n=== Paper Chunks ===")
        r = db.execute(text("SELECT COUNT(*) as cnt FROM data_paper_chunks"))
        print(f"Total chunks: {r.fetchone()[0]}")
        
        # Check chunks by paper
        r = db.execute(text("""
            SELECT metadata->>'paper_id' as paper_id, COUNT(*) as cnt 
            FROM data_paper_chunks 
            GROUP BY metadata->>'paper_id'
            LIMIT 10
        """))
        for row in r.fetchall():
            print(f"  Paper {row[0]}: {row[1]} chunks")
        
        # Check papers in project 43
        print("\n=== Papers in Project 43 ===")
        r = db.execute(text("""
            SELECT p.id, p.title 
            FROM papers p 
            JOIN project_papers pp ON pp.paper_id = p.id 
            WHERE pp.project_id = 43
        """))
        for row in r.fetchall():
            print(f"  Paper {row[0]}: {row[1][:50]}...")
            
        # Check methodology data
        print("\n=== Methodology Data ===")
        r = db.execute(text("""
            SELECT paper_id, methodology_description, approach_novelty, methodology_context
            FROM methodology_data WHERE project_id = 43
        """))
        for row in r.fetchall():
            print(f"  Paper {row[0]}:")
            print(f"    description: {row[1][:80] if row[1] else 'EMPTY'}...")
            print(f"    novelty: {row[2][:80] if row[2] else 'EMPTY'}...")
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_paper_data()
