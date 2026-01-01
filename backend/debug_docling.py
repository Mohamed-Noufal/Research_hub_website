"""
Debug Docling Output
Quick script to see what Docling returns from PDF parsing
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from docling.document_converter import DocumentConverter

# Use first PDF
pdf_dir = Path(__file__).parent / "uploads" / "pdfs" 
pdf_files = list(pdf_dir.glob("*.pdf"))

if not pdf_files:
    print("No PDFs found!")
    exit(1)

pdf_path = str(pdf_files[0])
print(f"Testing with: {pdf_path}")
print("="*60)

converter = DocumentConverter()
result = converter.convert(pdf_path)

print(f"\nDocument type: {type(result.document)}")
print(f"Has iterate_items: {hasattr(result.document, 'iterate_items')}")

# Check what the document object has
print(f"\nDocument attributes: {[a for a in dir(result.document) if not a.startswith('_')][:20]}")

# Try to get text content
if hasattr(result.document, 'export_to_markdown'):
    md = result.document.export_to_markdown()
    print(f"\nMarkdown preview (first 1000 chars):")
    print(md[:1000])
    print(f"\nTotal markdown length: {len(md)}")
elif hasattr(result.document, 'text'):
    print(f"\nText preview: {result.document.text[:1000]}")
else:
    print("\nNo text or markdown method found!")
    
# Try iterate_items
if hasattr(result.document, 'iterate_items'):
    print("\n\nIterating items (first 5):")
    count = 0
    for item in result.document.iterate_items():
        count += 1
        print(f"  Item {count}: type={type(item)}")
        print(f"           attrs={[a for a in dir(item) if not a.startswith('_')][:10]}")
        if hasattr(item, 'text'):
            print(f"           text={item.text[:100] if item.text else 'None'}...")
        if count >= 5:
            break
    print(f"\nTotal items: Counting...")
    total = sum(1 for _ in result.document.iterate_items())
    print(f"Total items: {total}")
