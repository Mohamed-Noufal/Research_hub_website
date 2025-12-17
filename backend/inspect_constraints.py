
import sys
import os
from sqlalchemy import create_engine, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use localhost credentials
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/paper_search"

def inspect_constraints():
    print("🔍 Inspecting Constraints...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            tables = ['methodology_data', 'findings']
            
            for table in tables:
                print(f"\n--- Table: {table} ---")
                # Query to get unique constraints
                query = text(f"""
                    SELECT conname, pg_get_constraintdef(c.oid)
                    FROM pg_constraint c
                    JOIN pg_namespace n ON n.oid = c.connamespace
                    WHERE c.conrelid = 'public.{table}'::regclass
                    AND c.contype = 'u'
                """)
                
                rows = connection.execute(query).fetchall()
                if not rows:
                    print(f"  ❌ No unique constraints found on '{table}'")
                else:
                    for row in rows:
                        print(f"  ✅ constraint: {row[0]} -> {row[1]}")
                        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_constraints()
