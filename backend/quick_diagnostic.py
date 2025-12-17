"""
Simple diagnostic to check literature review database state
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

def diagnose():
    print("="*70)
    print("LITERATURE REVIEW DATABASE DIAGNOSTIC")
    print("="*70)
    
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    try:
        # Check user_literature_reviews table
        print("\n1. Checking user_literature_reviews table...")
        result = conn.execute(text("""
            SELECT id, title, description, created_at, updated_at, paper_ids
            FROM user_literature_reviews
            LIMIT 5
        """))
        
        reviews = result.fetchall()
        print(f"   Found {len(reviews)} literature reviews")
        
        for review in reviews:
            print(f"\n   Review ID: {review[0]}")
            print(f"   Title: {review[1]}")
            print(f"   Created: {review[3]}")
            print(f"   Updated: {review[4]}")
            print(f"   Paper IDs: {review[5]}")
        
        # Check for NULL timestamps
        print("\n2. Checking for NULL timestamps...")
        result = conn.execute(text("""
            SELECT COUNT(*) as null_created, 
                   (SELECT COUNT(*) FROM user_literature_reviews WHERE updated_at IS NULL) as null_updated
            FROM user_literature_reviews 
            WHERE created_at IS NULL
        """))
        
        null_counts = result.fetchone()
        print(f"   Reviews with NULL created_at: {null_counts[0]}")
        print(f"   Reviews with NULL updated_at: {null_counts[1]}")
        
        # Check papers table
        print("\n3. Checking papers table...")
        result = conn.execute(text("""
            SELECT COUNT(*) FROM papers WHERE source = 'demo'
        """))
        demo_count = result.fetchone()[0]
        print(f"   Demo papers: {demo_count}")
        
        # Check project_papers
        print("\n4. Checking project_papers...")
        result = conn.execute(text("""
            SELECT project_id, COUNT(*) as paper_count
            FROM project_papers
            GROUP BY project_id
        """))
        
        projects = result.fetchall()
        print(f"   Projects with papers: {len(projects)}")
        for proj in projects:
            print(f"     Project {proj[0]}: {proj[1]} papers")
        
        # Check findings
        print("\n5. Checking findings...")
        result = conn.execute(text("""
            SELECT project_id, COUNT(*) as finding_count
            FROM findings
            GROUP BY project_id
        """))
        
        findings = result.fetchall()
        print(f"   Projects with findings: {len(findings)}")
        for proj in findings:
            print(f"     Project {proj[0]}: {proj[1]} findings")
        
        print("\n" + "="*70)
        print("DIAGNOSTIC COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    diagnose()
