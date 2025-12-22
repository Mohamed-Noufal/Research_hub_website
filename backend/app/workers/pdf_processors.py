"""
Background jobs for PDF processing
"""
import asyncio
import os
from app.core.rag_engine import RAGEngine
from app.core.database import SessionLocal
from sqlalchemy import text
from arq.connections import RedisSettings

async def process_pdf_job(ctx, paper_id: int, pdf_path: str, project_id: int = None):
    """
    Background task to process PDF with Docling
    """
    print(f"🔄 [Worker] Starting processing for Paper {paper_id}...")
    
    # Initialize RAG engine inside the worker process
    # Note: RAG engine initialization can be expensive (loading models).
    # In a production setup, we might want to load models at worker startup (see arq startup/shutdown hooks).
    # For now, simplistic initialization per job to ensure clean state.
    rag_engine = RAGEngine()
    
    try:
        # 1. Parse & Ingest with Docling
        # This is the CPU-intensive part that blocks the main thread if run synchronously
        stats = await rag_engine.ingest_paper_with_docling(
            paper_id=paper_id,
            pdf_path=pdf_path,
            metadata={'project_id': project_id}
        )
        
        # 2. Update Database Status
        db = SessionLocal()
        try:
            # Mark as processed clearly in the database
            # Assuming 'is_processed' column exists on papers table (Phase 1 migration should handle this)
            # If not, we might need to add it or use a separate 'status' table
            db.execute(
                text("UPDATE papers SET is_processed = TRUE, last_updated = NOW() WHERE id = :pid"),
                {'pid': paper_id}
            )
            db.commit()
        except Exception as db_err:
            print(f"⚠️ [Worker] Database update failed for Paper {paper_id}: {db_err}")
            # Don't fail the job if just the status update fails, but log it
            # In rigorous production, you'd want retry logic here
        finally:
            db.close()
            
        print(f"✅ [Worker] Finished Paper {paper_id}: {stats}")
        return stats
        
    except Exception as e:
        print(f"❌ [Worker] Failed Paper {paper_id}: {e}")
        # Ideally update DB with error status
        db = SessionLocal()
        try:
            db.execute(
                text("UPDATE papers SET is_processed = FALSE WHERE id = :pid"), # Or use an error flag/column
                {'pid': paper_id}
            )
            db.commit()
        except:
            pass
        finally:
            db.close()
        raise e

async def startup(ctx):
    print("🚀 [Worker] Starting up...")

async def shutdown(ctx):
    print("🛑 [Worker] Shutting down...")

# ARQ Worker Settings
class WorkerSettings:
    functions = [process_pdf_job]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
