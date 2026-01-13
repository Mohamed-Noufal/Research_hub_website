"""
Manual RAG Ingestion Script
Run this to ingest papers into the RAG vector store without needing Celery.
"""
import asyncio
import sys
from app.core.database import SessionLocal
from app.core.rag_engine import RAGEngine
from sqlalchemy import text

async def ingest_paper_rag(paper_id: int):
    """Ingest a single paper into RAG vector store"""
    db = SessionLocal()
    
    try:
        # Get paper info
        result = db.execute(text("""
            SELECT id, title, local_file_path, user_id 
            FROM papers WHERE id = :paper_id
        """), {'paper_id': paper_id})
        paper = result.fetchone()
        
        if not paper:
            print(f"❌ Paper {paper_id} not found")
            return False
            
        pdf_path = paper[2]
        if not pdf_path:
            print(f"❌ Paper {paper_id} has no PDF file path")
            return False
        
        print(f"📄 Processing paper {paper_id}: {paper[1][:50]}...")
        print(f"   PDF: {pdf_path}")
        
        # Initialize RAG engine
        rag_engine = RAGEngine()
        
        # Ingest paper
        stats = await rag_engine.ingest_paper_with_docling(
            paper_id=paper_id,
            pdf_path=pdf_path,
            user_id=str(paper[3]) if paper[3] else None,
            title=paper[1]
        )
        
        print(f"✅ Ingested {stats.get('text_chunks', 0)} chunks for paper {paper_id}")
        
        # Update paper status
        db.execute(text("""
            UPDATE papers SET is_processed = TRUE WHERE id = :paper_id
        """), {'paper_id': paper_id})
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

async def ingest_project_papers(project_id: int):
    """Ingest all papers in a project"""
    db = SessionLocal()
    
    try:
        result = db.execute(text("""
            SELECT p.id, p.title 
            FROM papers p 
            JOIN project_papers pp ON pp.paper_id = p.id 
            WHERE pp.project_id = :project_id
        """), {'project_id': project_id})
        papers = result.fetchall()
        
        print(f"📚 Found {len(papers)} papers in project {project_id}")
        
        for paper in papers:
            await ingest_paper_rag(paper[0])
            
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ingest_rag.py --paper 1741         # Ingest single paper")
        print("  python ingest_rag.py --project 43         # Ingest all papers in project")
        sys.exit(1)
    
    if sys.argv[1] == "--paper" and len(sys.argv) >= 3:
        paper_id = int(sys.argv[2])
        asyncio.run(ingest_paper_rag(paper_id))
    elif sys.argv[1] == "--project" and len(sys.argv) >= 3:
        project_id = int(sys.argv[2])
        asyncio.run(ingest_project_papers(project_id))
    else:
        print("Invalid arguments")
