
import sys
import os
from sqlalchemy import create_engine, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock settings/get_current_user_id to avoid imports
class Settings:
    # Try typical local URLs
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/paper_search" 
settings = Settings()

def inspect_schema():
    print("🔍 Inspecting Database Schema...")
    engine = create_engine(settings.DATABASE_URL)
    connection = engine.connect()
    
    tables_to_check = ['methodology_data', 'findings']
    
    for table in tables_to_check:
        print(f"\n--- Table: {table} ---")
        try:
            # Check if table exists
            exists = connection.execute(text(f"SELECT to_regclass('public.{table}')")).scalar()
            if not exists:
                print(f"❌ Table '{table}' does NOT exist!")
                continue
                
            # Get columns
            columns = connection.execute(text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)).fetchall()
            
            if not columns:
                print(f"⚠️ Table '{table}' exists but has no columns? (Permission issue maybe)")
            else:
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
                    
        except Exception as e:
            print(f"❌ Error inspecting {table}: {e}")
            import traceback
            traceback.print_exc()
            
    connection.close()

if __name__ == "__main__":
    inspect_schema()
