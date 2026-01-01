"""
Phase 0 Validation Script
Simple script to ingest 3 test papers and verify the RAG pipeline works.
Run this before implementing Celery to confirm the flow works.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.core.rag_engine import RAGEngine
from app.core.database import SessionLocal
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_test_paper(db, title: str, user_id: str) -> int:
    """Create a paper record in the database"""
    result = db.execute(
        text("""
            INSERT INTO papers (title, source, is_manual, user_id)
            VALUES (:title, 'test_upload', TRUE, :user_id)
            RETURNING id
        """),
        {"title": title, "user_id": user_id}
    )
    db.commit()
    paper_id = result.fetchone()[0]
    logger.info(f"Created paper record: id={paper_id}, title='{title}'")
    return paper_id


async def update_paper_status(db, paper_id: int, status: str, chunk_count: int = 0):
    """Update paper processing status - use is_processed column"""
    is_done = status == "completed"
    db.execute(
        text("""
            UPDATE papers 
            SET is_processed = :done
            WHERE id = :id
        """),
        {"done": is_done, "id": paper_id}
    )
    db.commit()


async def ingest_test_paper(rag_engine, db, pdf_path: str, user_id: str):
    """Ingest a single test paper"""
    filename = os.path.basename(pdf_path)
    title = filename.replace(".pdf", "").replace("_", " ").title()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {filename}")
    logger.info(f"{'='*60}")
    
    # 1. Create paper record
    paper_id = await create_test_paper(db, title, user_id)
    
    # 2. Ingest with Docling
    try:
        stats = await rag_engine.ingest_paper_with_docling(
            paper_id=paper_id,
            pdf_path=pdf_path,
            user_id=user_id,
            title=title,
            project_id=None
        )
        
        # 3. Update status
        await update_paper_status(db, paper_id, "completed", stats.get("text_chunks", 0))
        
        logger.info(f"SUCCESS: Paper {paper_id} ingested with {stats.get('text_chunks', 0)} chunks")
        return paper_id, stats
        
    except Exception as e:
        await update_paper_status(db, paper_id, "failed", 0)
        logger.error(f"FAILED: Paper {paper_id} - {e}")
        return paper_id, None


async def test_search(rag_engine, user_id: str, query: str):
    """Test search functionality"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing Search: '{query}'")
    logger.info(f"{'='*60}")
    
    results = await rag_engine.query(
        query_text=query,
        user_id=user_id,
        top_k=5
    )
    
    logger.info(f"Answer: {results['answer'][:200]}...")
    logger.info(f"Sources: {len(results['source_nodes'])} chunks retrieved")
    
    for i, node in enumerate(results['source_nodes'][:3]):
        logger.info(f"  [{i+1}] Paper: {node.get('metadata', {}).get('title', 'Unknown')}")
        logger.info(f"      Section: {node.get('section_type', 'Unknown')}")
        logger.info(f"      Score: {node.get('score', 0):.3f}")
    
    return results


async def verify_chunks_in_db(db):
    """Verify chunks exist in database"""
    result = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks"))
    count = result.fetchone()[0]
    logger.info(f"\nTotal chunks in database: {count}")
    return count


async def main():
    logger.info("="*60)
    logger.info("PHASE 0: VALIDATION TESTING")
    logger.info("="*60)
    
    # Test user ID - use a valid UUID format
    test_user_id = "00000000-0000-0000-0000-000000000001"
    
    # Find test PDFs
    pdf_dir = Path(__file__).parent / "uploads" / "pdfs"
    pdf_files = list(pdf_dir.glob("*.pdf"))[:3]  # Limit to 3
    
    if not pdf_files:
        # Create a sample PDF directory note
        logger.warning(f"No PDFs found in {pdf_dir}")
        logger.info("Please add 1-3 test PDFs to backend/uploads/pdfs/ and run again")
        logger.info("You can download sample papers from arXiv for testing")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Initialize
    db = SessionLocal()
    rag_engine = RAGEngine()
    
    try:
        # Step 1: Ingest papers
        logger.info("\n>>> STEP 1: Ingesting Papers")
        ingested_papers = []
        
        for pdf_path in pdf_files:
            paper_id, stats = await ingest_test_paper(
                rag_engine, db, str(pdf_path), test_user_id
            )
            if stats:
                ingested_papers.append(paper_id)
        
        if not ingested_papers:
            logger.error("No papers were successfully ingested!")
            return
        
        logger.info(f"\nIngested {len(ingested_papers)} papers successfully")
        
        # Step 2: Verify chunks
        logger.info("\n>>> STEP 2: Verifying Chunks in Database")
        chunk_count = await verify_chunks_in_db(db)
        
        if chunk_count == 0:
            logger.error("No chunks found in database! Ingestion may have failed.")
            return
        
        # Step 3: Test search
        logger.info("\n>>> STEP 3: Testing Search")
        
        test_queries = [
            "What methodologies are used in this research?",
            "What are the main findings?",
            "Explain the approach used"
        ]
        
        for query in test_queries:
            await test_search(rag_engine, test_user_id, query)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("VALIDATION COMPLETE")
        logger.info("="*60)
        logger.info(f"Papers ingested: {len(ingested_papers)}")
        logger.info(f"Total chunks: {chunk_count}")
        logger.info(f"Search working: YES")
        logger.info("\nYou can now proceed to Phase 1 (Celery) with confidence!")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
