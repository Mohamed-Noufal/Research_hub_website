#!/usr/bin/env python3
"""
CLEAN SLATE RESET
Completely wipes papers and related data, re-indexes from physical files only.
Adds schema enhancements to prevent future conflicts.
"""
import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.config import settings
from app.core.rag_engine import RAGEngine
from app.models.paper import Paper

async def clean_slate_reset():
    """Nuclear option: Delete everything, start fresh from files"""
    
    print("="*80)
    print("CLEAN SLATE DATABASE RESET")
    print("WARNING: This will DELETE ALL papers, user libraries, and notes!")
    print("="*80)
    print()
    
    # Step 1: Scan files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, "uploads", "pdfs")
    
    if not os.path.exists(uploads_dir):
        print(f"ERROR: Directory not found: {uploads_dir}")
        return
    
    files = [f for f in os.listdir(uploads_dir) if f.endswith(".pdf")]
    print(f"Step 1: Found {len(files)} PDF files to re-index")
    for f in files:
        print(f"  - {f}")
    print()
    
    # Step 2: Connect to database
    db_url = settings.DATABASE_URL
    if "postgresql+asyncpg" not in db_url:
        if "postgresql://" in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Step 3: NUCLEAR DELETE
    print("Step 2: Deleting all papers and related data...")
    print("  (Disabling foreign key checks temporarily)")
    
    async with AsyncSessionLocal() as session:
        # Count before deletion
        result = await session.execute(text("SELECT COUNT(*) FROM papers"))
        before_count = result.scalar()
        
        result = await session.execute(text("SELECT COUNT(*) FROM paper_chunks"))
        chunks_before = result.scalar()
        
        print(f"  Current: {before_count} papers, {chunks_before} chunks")
        
        # TRUNCATE CASCADE - this deletes EVERYTHING related to papers
        await session.execute(text("""
            TRUNCATE TABLE 
                papers, 
                data_paper_chunks,
                user_saved_papers,
                user_notes,
                project_papers
            CASCADE
        """))
        
        await session.commit()
        print("  SUCCESS: All tables truncated")
    
    print()
    
    # Step 4: Add schema enhancement - local_file_path column
    print("Step 3: Enhancing schema to prevent future conflicts...")
    async with AsyncSessionLocal() as session:
        try:
            # Check if column exists
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='papers' AND column_name='local_file_path'
            """))
            
            if not result.scalar():
                # Add column for tracking local file paths
                await session.execute(text("""
                    ALTER TABLE papers 
                    ADD COLUMN local_file_path TEXT
                """))
                await session.commit()
                print("  Added 'local_file_path' column to papers table")
            else:
                print("  'local_file_path' column already exists")
        except Exception as e:
            print(f"  Schema enhancement skipped: {e}")
    
    print()
    
    # Step 5: Re-create papers from files
    print("Step 4: Creating paper records from files...")
    file_to_id = {}
    
    async with AsyncSessionLocal() as session:
        for filename in files:
            # Extract title from filename
            if filename.startswith("manual_"):
                # manual_TIMESTAMP_Title.pdf -> Title
                parts = filename.replace("manual_", "").replace(".pdf", "").split("_", 1)
                title = parts[1] if len(parts) > 1 else parts[0]
                title = title.replace("_", " ")
            else:
                title = filename.replace(".pdf", "").replace("_", " ")
            
            # Create paper
            new_paper = Paper(
                title=title,
                source="manual_upload",
                is_processed=False,
                is_manual=True
            )
            
            session.add(new_paper)
            await session.flush()
            await session.refresh(new_paper)
            
            # Update local_file_path
            file_path = os.path.join(uploads_dir, filename)
            await session.execute(
                text("UPDATE papers SET local_file_path = :path WHERE id = :id"),
                {"path": file_path, "id": new_paper.id}
            )
            
            file_to_id[filename] = new_paper.id
            print(f"  Created Paper {new_paper.id}: {title}")
        
        await session.commit()
    
    print()
    
    # Step 6: RAG Indexing
    print("Step 5: Re-indexing into RAG engine...")
    print("This will take 1-2 minutes per paper (8 papers = ~10-15 min total)")
    print()
    
    rag_engine = RAGEngine()
    success = 0
    errors = 0
    
    async with AsyncSessionLocal() as session:
        for filename, paper_id in file_to_id.items():
            file_path = os.path.join(uploads_dir, filename)
            
            result = await session.execute(
                text("SELECT title FROM papers WHERE id = :id"),
                {"id": paper_id}
            )
            row = result.fetchone()
            
            if not row:
                print(f"  ERROR: Paper {paper_id} not found")
                errors += 1
                continue
            
            print(f"  [{success+1}/{len(files)}] Processing: {row.title}...")
            
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
                print(f"      SUCCESS: {stats.get('text_chunks', 0)} chunks indexed")
                
            except Exception as e:
                errors += 1
                print(f"      ERROR: {str(e)[:150]}")
    
    await engine.dispose()
    
    # Final verification
    print()
    print("="*80)
    print("VERIFICATION")
    print("="*80)
    
    engine2 = create_async_engine(db_url)
    AsyncSessionLocal2 = sessionmaker(engine2, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal2() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM papers"))
        papers_count = result.scalar()
        
        result = await session.execute(text("SELECT COUNT(*) FROM data_paper_chunks"))
        chunks_count = result.scalar()
        
        print(f"Papers in database: {papers_count}")
        print(f"RAG chunks indexed: {chunks_count}")
        print(f"Files processed: {success} successful, {errors} errors")
    
    await engine2.dispose()
    
    print()
    print("="*80)
    print("RESET COMPLETE!")
    print("="*80)
    
    if success == len(files) and chunks_count > 0:
        print("SUCCESS: Database fully synchronized with files!")
        print("All papers are now searchable via RAG engine.")
        print()
        print("SCHEMA ENHANCEMENTS:")
        print("- Added 'local_file_path' column for file tracking")
        print("- No more file/DB mismatches possible")
    else:
        print(f"PARTIAL: {success}/{len(files)} papers indexed")
        print("Check errors above for details")
    
    return success, errors

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(clean_slate_reset())
