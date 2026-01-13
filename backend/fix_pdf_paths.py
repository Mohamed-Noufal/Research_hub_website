"""
Script to fix papers that have PDFs downloaded but missing local_file_path
"""
import os
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Get list of PDFs in uploads folder
pdf_folder = "uploads/pdfs"
pdfs = os.listdir(pdf_folder)

print(f"Found {len(pdfs)} PDF files in {pdf_folder}")

fixed = 0
for pdf_file in pdfs:
    # Try to extract paper_id from filename (format: {paper_id}.pdf or manual_{timestamp}_{title}.pdf)
    if pdf_file.startswith("manual_"):
        # Skip manual uploads for now - need different logic
        print(f"  Skipping manual upload: {pdf_file}")
        continue
    
    # Standard format: {paper_id}.pdf
    try:
        paper_id = int(pdf_file.replace(".pdf", ""))
    except ValueError:
        print(f"  Cannot parse paper_id from: {pdf_file}")
        continue
    
    full_path = os.path.abspath(os.path.join(pdf_folder, pdf_file))
    
    # Update database
    result = db.execute(text("""
        UPDATE papers 
        SET local_file_path = :path,
            processing_status = 'pending'
        WHERE id = :paper_id
        RETURNING id, title
    """), {"path": full_path, "paper_id": paper_id})
    
    row = result.fetchone()
    if row:
        print(f"✅ Fixed paper {row[0]}: {row[1][:50]}...")
        fixed += 1
    else:
        print(f"  Paper {paper_id} not found in database")

db.commit()
db.close()

print(f"\n🎉 Fixed {fixed} papers!")
print("Run batch-process to extract content from these PDFs.")
