#!/usr/bin/env python
"""
 atabase eset & estore
emoves orphaned papers while preserving user data (libraries, notes, annotations)
"""
import asyncio
import os
import sys
from typing import ict, ist, et
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, syncession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.rag_engine import ngine
from app.models.paper import aper
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

# orce unbuffered output
sys.stdout  os.fdopen(sys.stdout.fileno(), 'w', buffering)
sys.stderr  os.fdopen(sys.stderr.fileno(), 'w', buffering)

# onfigure logging with immediate flush
logging.basiconfig(
    levellogging., 
    format'%(asctime)s - %(levelname)s - %(message)s',
    handlers
        logging.treamandler(sys.stdout)
    ]
)
logger  logging.getogger(__name__)

# orce immediate flush on all log calls
class lushandler(logging.treamandler)
    def emit(self, record)
        super().emit(record)
        self.flush()

logger.handlers  lushandler(sys.stdout)]
logger.setevel(logging.)

async def safe_reset_and_restore()
    """
     eset trategy
    . can physical files in uploads/pdfs
    . xtract valid paper s from filenames
    . elete  papers  in the valid list (preserves user data for valid papers)
    . nsure  records exist for all physical files
    . e-index all files into  engine
    """
    
    logger.info("" * )
    logger.info("   & ")
    logger.info("" * )
    
    # tep  can physical files
    base_dir  os.path.dirname(os.path.abspath(__file__))
    uploads_dir  os.path.join(base_dir, "uploads", "pdfs")
    
    if not os.path.exists(uploads_dir)
        logger.error(f"❌ ploads directory not found {uploads_dir}")
        return
    
    files  f for f in os.listdir(uploads_dir) if f.endswith(".pdf")]
    logger.info(f"📂 ound {len(files)} physical  files")
    
    # tep  xtract valid paper s and create file mapping
    file_to_id ictstr, int]  {}  # filename - paper_id
    valid_paper_ids etint]  set()
    
    for filename in files
        paper_id  one
        
        if filename.startswith("manual_")
            # ormat manual__itle.pdf or manual__itle.pdf
            parts  filename.split("_")
            if len(parts)   and parts].isdigit()
                # heck if it's a real paper  or timestamp
                potential_id  int(parts])
                # f  , likely a timestamp, not a paper 
                if potential_id  
                    paper_id  potential_id
        elif filename-].isdigit()
            # ormat .pdf
            paper_id  int(filename-])
        
        if paper_id
            file_to_idfilename]  paper_id
            valid_paper_ids.add(paper_id)
            logger.info(f"  ✓ {filename} → aper  {paper_id}")
        else
            logger.warning(f"  ⚠ {filename} → annot extract paper  (will treat as new)")
    
    logger.info(f"📋 alid aper s extracted {len(valid_paper_ids)}")
    
    # tep  atabase connection
    db_url  settings._
    if "postgresql+asyncpg" not in db_url
        if "postgresql//" in db_url
            db_url  db_url.replace("postgresql//", "postgresql+asyncpg//")
    
    engine  create_async_engine(db_url)
    syncessionocal  sessionmaker(engine, class_syncession, expire_on_commitalse)
    
    # tep  ackup metadata for valid papers
    metadata_backup ictint, dict]  {}
    
    logger.info("💾 tep  acking up metadata for valid papers...")
    async with syncessionocal() as session
        if valid_paper_ids
            # etch metadata for each paper individually to avoid complex 
            for paper_id in valid_paper_ids
                result  await session.execute(
                    text("""
                         id, title, abstract, authors, project_id, pdf_url, 
                               source, arxiv_id, doi, venue, citation_count
                         papers 
                         id  id
                    """),
                    {"id" paper_id}
                )
                row  result.fetchone()
                
                if row
                    metadata_backuprow.id]  {
                        "title" row.title or "nknown itle",
                        "abstract" row.abstract,
                        "authors" row.authors,
                        "project_id" row.project_id or ,
                        "pdf_url" row.pdf_url,
                        "source" row.source or "manual_upload",
                        "arxiv_id" row.arxiv_id,
                        "doi" row.doi,
                        "venue" row.venue,
                        "citation_count" row.citation_count or 
                    }
            
            logger.info(f"  ✓ acked up metadata for {len(metadata_backup)} papers")
    
    # tep  ount orphaned papers
    logger.info("🔍 tep  dentifying orphaned papers...")
    async with syncessionocal() as session
        result  await session.execute(text(" (*)  papers"))
        total_papers  result.scalar()
        
        orphaned_count  total_papers - len(valid_paper_ids)
        logger.info(f"  otal papers in  {total_papers}")
        logger.info(f"  alid papers (with files) {len(valid_paper_ids)}")
        logger.info(f"  rphaned papers (no files) {orphaned_count}")
    
    # tep  elete orphaned papers ( - preserves user data for valid papers)
    if orphaned_count  
        logger.info("🧹 tep  eleting orphaned papers...")
        logger.warning(f"  ⚠️ his will delete {orphaned_count} papers that have no physical files")
        logger.info("  ✓ ser data (libraries, notes) for valid papers will be preserved")
        
        async with syncessionocal() as session
            if valid_paper_ids
                # et all paper s
                result  await session.execute(text(" id  papers"))
                all_ids  {row] for row in result.fetchall()}
                
                # ind orphans (s not in valid list)
                orphan_ids  all_ids - valid_paper_ids
                
                if orphan_ids
                    # elete orphaned papers one by one
                    deleted_count  
                    for orphan_id in orphan_ids
                        await session.execute(
                            text("  papers  id  id"),
                            {"id" orphan_id}
                        )
                        deleted_count + 
                    
                    await session.commit()
                    logger.info(f"  ✓ eleted {deleted_count} orphaned papers")
                else
                    logger.info("  ✓ o orphaned papers found")
            else
                # o valid papers - delete all (but this shouldn't happen if files exist)
                result  await session.execute(text("  papers  id"))
                deleted_ids  row] for row in result.fetchall()]
                await session.commit()
                logger.info(f"  ✓ eleted {len(deleted_ids)} papers")
    else
        logger.info("✓ tep  o orphaned papers to delete")
    
    # tep  nsure  records exist for all physical files
    logger.info("📝 tep  nsuring  records for all physical files...")
    
    async with syncessionocal() as session
        for filename in files
            file_path  os.path.join(uploads_dir, filename)
            
            # et or create paper 
            if filename in file_to_id
                paper_id  file_to_idfilename]
                
                # heck if record still exists
                result  await session.execute(
                    text(" id  papers  id  id"),
                    {"id" paper_id}
                )
                exists  result.scalar()
                
                if exists
                    logger.info(f"  ✓ {filename} → aper {paper_id} (exists)")
                    continue
                else
                    # ecord was deleted (shouldn't happen with our logic, but handle it)
                    logger.warning(f"  ⚠ {filename} → aper {paper_id} deleted, will recreate")
            
            # reate new paper record
            # se backed up metadata if available, otherwise create minimal record
            paper_id_for_lookup  file_to_id.get(filename)
            metadata  metadata_backup.get(paper_id_for_lookup, {})
            
            # xtract title from filename if no metadata
            if not metadata.get("title")
                title  filename.replace("manual_", "").replace(".pdf", "").replace("_", " ")
                # emove timestamp prefix if present (e.g., " itle" - "itle")
                parts  title.split(" ", )
                if parts].isdigit() and len(parts)  
                    title  parts]
            else
                title  metadata"title"]
            
            new_paper  aper(
                titletitle,
                abstractmetadata.get("abstract"),
                authorsmetadata.get("authors"),
                project_idmetadata.get("project_id", ),
                pdf_urlmetadata.get("pdf_url"),
                sourcemetadata.get("source", "manual_upload"),
                arxiv_idmetadata.get("arxiv_id"),
                doimetadata.get("doi"),
                venuemetadata.get("venue"),
                citation_countmetadata.get("citation_count", ),
                is_processedalse,
                is_manualrue
            )
            
            session.add(new_paper)
            await session.flush()
            await session.refresh(new_paper)
            
            new_id  new_paper.id
            logger.info(f"  ✓ {filename} → reated aper {new_id} {title}")
            
            # pdate mapping for ingestion phase
            file_to_idfilename]  new_id
            
        await session.commit()
    
    # tep  e-index all papers into  engine
    logger.info("🚀 tep  e-indexing papers into  engine...")
    rag_engine  ngine()
    
    success_count  
    error_count  
    
    async with syncessionocal() as session
        for filename, paper_id in file_to_id.items()
            file_path  os.path.join(uploads_dir, filename)
            
            # et paper metadata
            result  await session.execute(
                text(" title, project_id  papers  id  id"),
                {"id" paper_id}
            )
            row  result.fetchone()
            
            if not row
                logger.error(f"  ❌ aper {paper_id} not found in  (skipping)")
                continue
            
            logger.info(f"  🔄 rocessing aper {paper_id} {row.title}")
            
            try
                ingest_metadata  {
                    "project_id" row.project_id,
                    "title" row.title
                }
                
                stats  await rag_engine.ingest_paper_with_docling(
                    paper_idpaper_id,
                    pdf_pathfile_path,
                    metadataingest_metadata
                )
                
                # ark as processed
                await session.execute(
                    text(" papers  is_processed    id  id"),
                    {"id" paper_id}
                )
                await session.commit()
                
                success_count + 
                logger.info(f"  ✅ uccess {stats}")
                
            except xception as e
                error_count + 
                logger.error(f"  ❌ ailed {str(e)}")
    
    await engine.dispose()
    
    # inal summary
    logger.info("" * )
    logger.info(" !")
    logger.info("" * )
    logger.info(f"📊 ummary")
    logger.info(f"  • hysical files processed {len(files)}")
    logger.info(f"  • uccessfully indexed {success_count}")
    logger.info(f"  • rrors {error_count}")
    logger.info(f"  • rphaned papers deleted {orphaned_count}")
    logger.info("")
    logger.info("✅ atabase is now synchronized with physical files!")
    logger.info("✅ ser data (libraries, notes) preserved for valid papers!")

if __name__  "__main__"
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
    
    if sys.platform  "win"
        asyncio.set_event_loop_policy(asyncio.indowselectorventoopolicy())
    
    asyncio.run(safe_reset_and_restore())
