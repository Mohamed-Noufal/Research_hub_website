
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from app.core.config import settings

print(f"Connecting to: {settings.DATABASE_URL}")
engine = create_engine(settings.DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Connected!")
        # Check paper_chunks
        target_tables = ["data_paper_chunks", "paper_chunks"]
        
        for table in target_tables:
            print(f"\nChecking table: {table}")
            try:
                # Check if table exists
                exists = conn.execute(text(f"SELECT to_regclass('public.{table}')")).scalar()
                if not exists:
                    print(f"Table {table} does not exist.")
                    continue
                    
                # Get columns
                result = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"))
                rows = list(result)
                if not rows:
                     print("No columns found (or permission issue).")
                for row in rows:
                    print(f" - {row[0]} ({row[1]})")
            except Exception as e:
                print(f"Error checking {table}: {e}")
                
except Exception as e:
    print(f"Connection failed: {e}")
