"""
Apply all remaining fixes to API files
"""
import os
import re

def fix_methodology():
    """Fix the corrupted methodology.py file"""
    file_path = 'app/api/v1/methodology.py'
    
    print("Fixing methodology.py...")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the broken query execution line
    content = re.sub(
        r'result = db\.execute\(query,',
        r'result = db.execute(text(query),',
        content
    )
    
    # Ensure sqlalchemy.text is imported
    if 'from sqlalchemy import text' not in content:
        content = content.replace(
            'from sqlalchemy.orm import Session',
            'from sqlalchemy.orm import Session\nfrom sqlalchemy import text'
        )
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ methodology.py fixed")

def fix_synthesis():
    """Add text() wrappers to synthesis.py"""
    file_path = 'app/api/v1/synthesis.py'
    
    print("\nFixing synthesis.py...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix structure query
    content = content.replace(
        'structure = db.execute(\n        structure_query,',
        'structure = db.execute(\n        text(structure_query),'
    )
    
    # Fix cells query
    content = content.replace(
        'cells = db.execute(\n        cells_query,',
        'cells = db.execute(\n        text(cells_query),'
    )
    
    # Ensure text is imported
    if 'from sqlalchemy import text' not in content:
        content = content.replace(
            'from sqlalchemy.orm import Session',
            'from sqlalchemy.orm import Session\nfrom sqlalchemy import text'
        )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ synthesis.py fixed")

def fix_analysis():
    """Add text() wrappers to analysis.py"""
    file_path = 'app/api/v1/analysis.py'
    
    print("\nFixing analysis.py...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix query execution
    content = content.replace(
        'result = db.execute(\n        query,',
        'result = db.execute(\n        text(query),'
    )
    
    # Ensure text is imported
    if 'from sqlalchemy import text' not in content:
        content = content.replace(
            'from sqlalchemy.orm import Session',
            'from sqlalchemy.orm import Session\nfrom sqlalchemy import text'
        )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ analysis.py fixed")

def fix_comparison():
    """Fix comparison.py response structure"""
    file_path = 'app/api/v1/comparison.py'
    
    print("\nFixing comparison.py...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the response to match the new schema
    old_response = '''    if result:
        return {
            "selected_paper_ids": result.selected_paper_ids or [],
            "insights_similarities": result.insights_similarities or "",
            "insights_differences": result.insights_differences or ""
        }
    
    return {
        "selected_paper_ids": [],
        "insights_similarities": "",
        "insights_differences": ""
    }'''
    
    new_response = '''    if result:
        return {
            "selected_paper_ids": result.selected_papers or [],
            "insights_similarities": result.insights_similarities or "",
            "insights_differences": result.insights_differences or ""
        }
    
    return {
        "selected_paper_ids": [],
        "insights_similarities": "",
        "insights_differences": ""
    }'''
    
    content = content.replace(old_response, new_response)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ comparison.py fixed")

def main():
    print("="*70)
    print("APPLYING FINAL API FIXES")
    print("="*70)
    
    try:
        fix_methodology()
        fix_synthesis()
        fix_analysis()
        fix_comparison()
        
        print("\n" + "="*70)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("="*70)
        print("\nNext step: Restart the uvicorn server to pick up changes")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
