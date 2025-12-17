import sys
import os
from sqlalchemy import text
sys.path.append(os.getcwd())
from app.core.database import engine

def debug_saved_papers():
    print("🔍 Debugging saved papers...")
    with engine.connect() as connection:
        # Get all saved papers with their paper details
        result = connection.execute(text("""
            SELECT 
                usp.id,
                usp.user_id,
                usp.paper_id,
                usp.saved_at,
                p.title,
                p.publication_date,
                p.date_added,
                p.last_updated
            FROM user_saved_papers usp
            JOIN papers p ON usp.paper_id = p.id
            WHERE usp.user_id = '550e8400-e29b-41d4-a716-446655440000'
        """))
        
        rows = result.fetchall()
        print(f"\nFound {len(rows)} saved papers:")
        for row in rows:
            print(f"\nPaper ID: {row[2]}")
            print(f"  Title: {row[4]}")
            print(f"  saved_at: {row[3]} (type: {type(row[3])})")
            print(f"  publication_date: {row[5]} (type: {type(row[5])})")
            print(f"  date_added: {row[6]} (type: {type(row[6])})")
            print(f"  last_updated: {row[7]} (type: {type(row[7])})")

if __name__ == "__main__":
    debug_saved_papers()
