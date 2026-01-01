#!/usr/bin/env python3
"""
Simplified Database Reset & Restore
Windows-compatible, no fancy logging, proven SQL patterns
"""
import asyncio
import os
import sys
from typing import Dict, Set
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.config import settings
from app.core.rag_engine import RAGEngine
from app.models.paper import Paper

async def simple_reset():
    """Simple reset: scan files, clean orphans, re-index"""
    
    print("="*80)
    print("DATABASE RESET & RESTORE")
    print("="*80)
    print()
    
    # Step 1: Scan files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, "uploads", "pdfs")
    
    if not os.path.exists(uploads_dir):
        print(f"ERROR: Directory not found: {uploads_dir}")
        return
    
    files = [f for f in os.listdir(uploads_dir) if f.endswith(".pdf")]
    print(f"Step 1: Found {len(files)} PDF files")
    print()
    
    # Step 2: Extract IDs from filenames
    file_to_id: Dict[str, int] = {}
    valid_ids: Set[int] = set()
    
    for filename in files:
        paper_id = None
        
        if filename.startswith("manual_"):
            parts = filename.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                potential_id = int(parts[1])
                if potential_id < 100000:  # Not a timestamp
                    paper_id = potential_id
        elif filename[:-4].isdigit():
            paper_id = int(filename[:-4])
        
        if paper_id:
            file_to_id[filename] = paper_id
            valid_ids.add(paper_id)
            print(f"  {filename} -> Paper ID {paper_id}")
    
    print(f"\nStep 2: Extracted {len(valid_ids)} valid paper IDs")
    print()
    
    # Step 3: Database connection
    db_url = settings.DATABASE_URL
    if "postgresql+asyncpg" not in db_url:
        if "postgresql://" in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Step 4: Backup metadata
    metadata_backup: Dict[int, dict] = {}
    
    print("Step 3: Backing up metadata...")
    async with AsyncSessionLocal() as session:
        for paper_id in valid_ids:
            result = await session.execute(
                text("SELECT id, title FROM papers WHERE id = :id"),
                {"id": paper_id}
            )
            row = result.fetchone()
            if row:
                metadata_backup[row.id] = {
                    "title": row.title or "Unknown"
                }
    
    print(f"  Backed up {len(metadata_backup)} papers")
    print()
    
    # Step 5: Delete orphans
    print("Step 4: Cleaning orphaned papers...")
    async with AsyncSessionLocal() as session:
        # Get all IDs
        result = await session.execute(text("SELECT id FROM papers"))
        all_ids = {row[0] for row in result.fetchall()}
        
        # Find orphans
        orphan_ids = all_ids - valid_ids
        
        print(f"  Total papers in DB: {len(all_ids)}")
        print(f"  Valid papers (with files): {len(valid_ids)}")
        print(f"  Orphaned papers: {len(orphan_ids)}")
        
        if orphan_ids:
            deleted = 0
            for orphan_id in orphan_ids:
                await session.execute(
                    text("DELETE FROM papers WHERE id = :id"),
                    {"id": orphan_id}
                )
                deleted += 1
            
            await session.commit()
            print(f"  Deleted {deleted} orphaned papers")
        else:
            print("  No orphans to delete")
    
    print()
    
    # Step 6: Ensure all files have DB records
    print("Step 5: Ensuring DB records for all files...")
    async with AsyncSessionLocal() as session:
        for filename in files:
            if filename in file_to_id:
                paper_id = file_to_id[filename]
                
                # Check if exists
                result = await session.execute(
                    text("SELECT id FROM papers WHERE id = :id"),
                    {"id": paper_id}
                )
                if result.scalar():
                    print(f"  {filename} -> Paper {paper_id} [exists]")
                    continue
            
            # Create new record
            meta = metadata_backup.get(file_to_id.get(filename), {})
            title = meta.get("title") or filename.replace(".pdf", "").replace("_", " ")
            
            new_paper = Paper(
                title=title,
                source="manual_upload",
                is_processed=False,
                is_manual=True
            )
            
            session.add(new_paper)
            await session.flush()
            await session.refresh(new_paper)
            
            print(f"  {filename} -> Created Paper {new_paper.id}")
            file_to_id[filename] = new_paper.id
        
        await session.commit()
    
    print()
    
    # Step 7: Re-index
    print("Step 6: Re-indexing into RAG engine...")
    print("This will take 1-2 minutes per paper (Docling + embeddings)")
    print()
    
    rag_engine = RAGEngine()
    success = 0
    errors = 0
    
    async with AsyncSessionLocal() as session:
        for filename, paper_id in file_to_id.items():
            file_path = os.path.join(uploads_dir, filename)
            
            # Get metadata
            result = await session.execute(
                text("SELECT title FROM papers WHERE id = :id"),
                {"id": paper_id}
            )
            row = result.fetchone()
            
            if not row:
                print(f"  ERROR: Paper {paper_id} not found")
                errors += 1
                continue
            
            print(f"  Processing Paper {paper_id}: {row.title}...")
            
            try:
                stats = await rag_engine.ingest_paper_with_docling(
                    paper_id=paper_id,
                    pdf_path=file_path,
                    metadata={"paper_id": paper_id, "title": row.title}
                )
                
                await session.execute(
                    text("UPDATE papers SET is_processed = TRUE WHERE id = :id"),
                    {"id": paper_id}
                )
                await session.commit()
                
                success += 1
                print(f"    SUCCESS: {stats}")
                
            except Exception as e:
                errors += 1
                print(f"    ERROR: {str(e)[:100]}")
    
    await engine.dispose()
    
    # Summary
    print()
    print("="*80)
    print("RESET COMPLETE")
    print("="*80)
    print(f"Files processed: {len(files)}")
    print(f"Successfully indexed: {success}")
    print(f"Errors: {errors}")
    print()
    if success > 0:
        print("SUCCESS: Database synchronized with files!")
        print("Your papers are now searchable in the RAG engine.")
    
    return success, errors

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(simple_reset())
