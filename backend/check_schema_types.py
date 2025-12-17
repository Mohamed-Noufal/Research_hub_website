"""
Check database schema to determine papers.id type and create appropriate fix
"""
import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/paper_search"

def check_schema():
    print("Checking database schema...")
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    try:
        # Check papers.id type
        result = conn.execute(text("""
            SELECT data_type, udt_name, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'papers' AND column_name = 'id'
        """))
        
        papers_id_info = result.fetchone()
        print(f"\npapers.id type: {papers_id_info}")
        
        # Check findings.paper_id type
        result = conn.execute(text("""
            SELECT data_type, udt_name, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'findings' AND column_name = 'paper_id'
        """))
        
        findings_paper_id_info = result.fetchone()
        print(f"findings.paper_id type: {findings_paper_id_info}")
        
        # Check methodology_data.paper_id type
        result = conn.execute(text("""
            SELECT data_type, udt_name, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'methodology_data' AND column_name = 'paper_id'
        """))
        
        methodology_paper_id_info = result.fetchone()
        print(f"methodology_data.paper_id type: {methodology_paper_id_info}")
        
        # Check project_papers.paper_id type
        result = conn.execute(text("""
            SELECT data_type, udt_name, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'project_papers' AND column_name = 'paper_id'
        """))
        
        project_papers_paper_id_info = result.fetchone()
        print(f"project_papers.paper_id type: {project_papers_paper_id_info}")
        
        print("\n" + "="*70)
        print("ANALYSIS:")
        print("="*70)
        
        papers_type = papers_id_info[1] if papers_id_info else "unknown"
        
        if papers_type == "uuid":
            print("\npapers.id is UUID")
            print("\nRECOMMENDED FIX:")
            print("1. Change findings.paper_id from TEXT to UUID")
            print("2. Change methodology_data.paper_id from TEXT to UUID")
            print("\nSQL Migration:")
            print("""
-- Fix findings table
ALTER TABLE findings ALTER COLUMN paper_id TYPE UUID USING paper_id::uuid;

-- Fix methodology_data table  
ALTER TABLE methodology_data ALTER COLUMN paper_id TYPE UUID USING paper_id::uuid;
            """)
        elif papers_type in ("int4", "integer"):
            print("\npapers.id is INTEGER")
            print("\nRECOMMENDED FIX:")
            print("1. Change findings.paper_id from TEXT to INTEGER")
            print("2. Change methodology_data.paper_id from TEXT to INTEGER")
            print("\nSQL Migration:")
            print("""
-- Fix findings table
ALTER TABLE findings ALTER COLUMN paper_id TYPE INTEGER USING paper_id::integer;

-- Fix methodology_data table
ALTER TABLE methodology_data ALTER COLUMN paper_id TYPE INTEGER USING paper_id::integer;
            """)
        else:
            print(f"\nUnknown papers.id type: {papers_type}")
            print("Manual investigation required")
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_schema()
