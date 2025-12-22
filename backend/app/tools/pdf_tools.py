"""
Updated PDF tools using ARQ for background processing
"""
from typing import Dict, Optional, List
from arq import create_pool
from app.core.worker import get_redis_settings
from sqlalchemy import text
import hashlib

async def parse_pdf_background(
    pdf_path: str,
    paper_id: int,
    project_id: Optional[int] = None
) -> Dict:
    """
    Enqueue PDF parsing job to Redis
    Returns: Job ID and status
    """
    # Create Redis connection pool
    redis = await create_pool(await get_redis_settings())
    
    # Enqueue job
    job = await redis.enqueue_job(
        'process_pdf_job',
        paper_id=paper_id,
        pdf_path=pdf_path,
        project_id=project_id
    )
    
    # Close pool explicitly or let it close (arq pools are designed to be long-lived or context managed)
    # Ideally, we should reuse a pool in the application state, but for this tool function, we create/close.
    await redis.close()
    
    return {
        "status": "queued",
        "job_id": job.job_id,
        "message": "Paper is processing in background. You can continue working."
    }

async def check_job_status(job_id: str) -> Dict:
    """Check status of background job"""
    redis = await create_pool(await get_redis_settings())
    job = await redis.get_job(job_id)
    
    if not job:
        await redis.close()
        return {"status": "unknown/not_found"}
        
    status = await job.status()
    
    result = None
    if status == 'complete':
        try:
            result = await job.result()
        except Exception as e:
            result = {"error": str(e)}
            
    await redis.close()
    
    return {
        "status": str(status),
        "result": result
    }

async def check_paper_exists(
    doi: Optional[str] = None,
    title: Optional[str] = None,
    db = None
) -> Optional[Dict]:
    """
    Check if paper exists in YOUR papers table
    
    Args:
        doi: DOI to check
        title: Title to check
        db: Database session
    
    Returns:
        Paper dict if exists, None otherwise
    """
    if doi:
        result = await db.execute(
            text("SELECT * FROM papers WHERE doi = :doi"),
            {'doi': doi}
        )
        row = result.fetchone()
        if row:
            return dict(row._mapping)
    
    if title:
        # Generate hash for deduplication
        title_hash = hashlib.md5(title.lower().encode()).hexdigest()
        result = await db.execute(
            text("SELECT * FROM papers WHERE paper_hash = :hash"),
            {'hash': title_hash}
        )
        row = result.fetchone()
        if row:
            return dict(row._mapping)
    
    return None

async def store_paper(
    title: str,
    authors: List[str],
    abstract: str,
    doi: Optional[str] = None,
    source: str = "manual",
    db = None
) -> int:
    """
    Store paper in YOUR papers table
    
    Args:
        title: Paper title
        authors: List of authors
        abstract: Abstract text
        doi: Optional DOI
        source: Source (manual, arxiv, etc.)
        db: Database session
    
    Returns:
        Paper ID
    """
    # Generate hash for deduplication
    paper_hash = hashlib.md5(title.lower().encode()).hexdigest()
    
    # For authors, ensure it's a list or string suitable for DB
    # Expected type in DB might be TEXT[] or JSONB or TEXT. assuming TEXT[] or JSONB based on usage
    # If it's a TEXT column (serialized), join it.
    # Checking previous usages, it seems `authors` is likely a text column or array. 
    # Let's assume it's compatible with the passed list or we cast it.
    # Postgres Array syntax for params handled by driver usually, but to be safe with text:
    
    # Let's assume the DB expects an array or the driver handles the list
    
    result = await db.execute(
        text("""
            INSERT INTO papers (
                title, authors, abstract, doi, source, paper_hash, is_processed
            ) VALUES (
                :title, :authors, :abstract, :doi, :source, :hash, FALSE
            )
            ON CONFLICT (paper_hash) DO UPDATE SET
                title = EXCLUDED.title,
                authors = EXCLUDED.authors,
                abstract = EXCLUDED.abstract,
                doi = EXCLUDED.doi
            RETURNING id
        """),
        {
            'title': title,
            'authors': authors, # Ensure this matches DB schema (List[str] -> TEXT[] works with psycopg2/asyncpg usually)
            'abstract': abstract,
            'doi': doi,
            'source': source,
            'hash': paper_hash
        }
    )
    await db.commit()
    
    paper_id = result.fetchone()[0]
    return paper_id
