"""
Script to reset and process papers with local PDFs
"""
import asyncio
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Reset papers with local PDFs for content extraction
result = db.execute(text("""
    UPDATE papers 
    SET is_processed = FALSE, processing_status = 'pending'
    WHERE local_file_path IS NOT NULL AND local_file_path != ''
"""))
db.commit()
print(f"Reset {result.rowcount} papers for processing")

# Get papers to process
papers = db.execute(text("""
    SELECT id, title, local_file_path
    FROM papers 
    WHERE local_file_path IS NOT NULL AND local_file_path != ''
      AND is_processed = FALSE
""")).fetchall()

print(f"\nProcessing {len(papers)} papers...")

async def process_all():
    from app.core.pdf_extractor import process_and_store_pdf
    
    for paper in papers:
        print(f"\n📄 Processing paper {paper.id}: {paper.title[:50]}...")
        try:
            await process_and_store_pdf(
                db=db,
                paper_id=paper.id,
                pdf_path=paper.local_file_path,
                user_id=None
            )
            print(f"  ✅ Done!")
        except Exception as e:
            print(f"  ❌ Error: {e}")

asyncio.run(process_all())
db.close()
print("\n🎉 Processing complete!")
