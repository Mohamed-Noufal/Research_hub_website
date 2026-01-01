
import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.core.rag_engine import RAGEngine
import logging

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reindex_all_papers():
    """
    Re-indexes papers found in backend/uploads/pdfs using pure Async SQLAlchemy.
    """
    # 1. Setup paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, "uploads", "pdfs")
    
    if not os.path.exists(uploads_dir):
        logger.error(f"❌ Uploads directory not found: {uploads_dir}")
        return

    files = [f for f in os.listdir(uploads_dir) if f.endswith(".pdf")]
    logger.info(f"📂 Found {len(files)} PDF files in {uploads_dir}")
    
    # 2. Extract potential IDs
    paper_files = {} # id -> filename
    for filename in files:
        paper_id = None
        if filename.startswith("manual_"):
            parts = filename.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                paper_id = int(parts[1])
        elif filename[:-4].isdigit():
            paper_id = int(filename[:-4])
            
        if paper_id:
            paper_files[paper_id] = filename

    if not paper_files:
        logger.warning("⚠️ No identifiable papers found.")
        return

    # 3. Fetch Metadata (Async)
    metadata_map = {}
    
    # Use the async URL and force asyncpg
    db_url = settings.DATABASE_URL
    if "postgresql+asyncpg" not in db_url:
        # If it's just postgresql://, perform replacement to valid async scheme
        if "postgresql://" in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            # Fallback or error
            logger.warning(f"⚠️ URL scheme unexpected: {db_url}")

    engine = create_async_engine(db_url)
    
    try:
        async with engine.connect() as conn:
            for pid in paper_files.keys():
                try:
                    result = await conn.execute(
                        text("SELECT id, title, project_id FROM papers WHERE id = :id"),
                        {"id": pid}
                    )
                    row = result.fetchone()
                    if row:
                        metadata_map[row.id] = {
                            "title": row.title,
                            "project_id": row.project_id
                        }
                except Exception as ex:
                    logger.warning(f"Failed to fetch metadata for ID {pid}: {ex}")
                    
        logger.info(f"📚 Fetched metadata for {len(metadata_map)} papers")
        
    except Exception as e:
        logger.error(f"❌ DB Error during metadata fetch: {e}")
        return
    finally:
        await engine.dispose()

    # 4. Ingest (Async)
    rag_engine = RAGEngine()
    
    for paper_id, meta in metadata_map.items():
        filename = paper_files[paper_id]
        file_path = os.path.join(uploads_dir, filename)
        
        logger.info(f"🚀 Ingesting Paper {paper_id}: {meta['title']}")
        
        try:
            # Metadata for filters
            ingest_metadata = {
                "project_id": meta["project_id"],
                "title": meta["title"]
            }
            
            stats = await rag_engine.ingest_paper_with_docling(
                paper_id=paper_id,
                pdf_path=file_path,
                metadata=ingest_metadata
            )
            logger.info(f"✅ Success: {stats}")
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest {filename}: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(reindex_all_papers())
