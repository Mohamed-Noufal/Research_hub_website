import sys
import os
from sqlalchemy import text
sys.path.append(os.getcwd())
from app.core.database import engine

def inspect_table():
    print("🔍 Inspecting papers table schema...")
    with engine.connect() as connection:
        result = connection.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'papers'"
        ))
        columns = [row[0] for row in result.fetchall()]
        
        required = [
            "user_id", "title", "abstract", "authors", "publication_date",
            "doi", "venue", "pdf_url", "source", "is_manual", "citation_count"
        ]
        
        print("\nColumn Check:")
        for col in required:
            status = "✅" if col in columns else "❌"
            print(f"{status} {col}")

if __name__ == "__main__":
    inspect_table()
