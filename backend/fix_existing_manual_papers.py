import sys
import os
from sqlalchemy import text
sys.path.append(os.getcwd())
from app.core.database import engine

def fix_existing_manual_papers():
    """Add existing manual papers to user_saved_papers table"""
    print("🔧 Fixing existing manual papers...")
    
    with engine.connect() as connection:
        # Find all manual papers that aren't in user_saved_papers
        result = connection.execute(text("""
            SELECT p.id, p.user_id, p.title
            FROM papers p
            WHERE p.is_manual = TRUE
            AND p.user_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM user_saved_papers usp
                WHERE usp.paper_id = p.id
                AND usp.user_id = p.user_id
            )
        """))
        
        papers_to_fix = result.fetchall()
        
        if not papers_to_fix:
            print("✅ No manual papers need fixing - all are already in saved papers!")
            return
        
        print(f"\n📝 Found {len(papers_to_fix)} manual papers to add to saved papers:")
        
        for paper in papers_to_fix:
            paper_id, user_id, title = paper
            print(f"  - Paper ID {paper_id}: {title}")
            
            # Add to user_saved_papers
            connection.execute(text("""
                INSERT INTO user_saved_papers (user_id, paper_id)
                VALUES (:user_id, :paper_id)
            """), {"user_id": user_id, "paper_id": paper_id})
        
        connection.commit()
        print(f"\n✅ Successfully added {len(papers_to_fix)} manual papers to saved papers!")

if __name__ == "__main__":
    try:
        fix_existing_manual_papers()
    except Exception as e:
        print(f"\n❌ Error: {e}")
