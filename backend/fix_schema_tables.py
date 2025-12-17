
import sys
import os
from sqlalchemy import create_engine, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use the credentials we inferred/saw
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/paper_search"

def fix_schema():
    print("🛠️ Starting Schema Repair...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            
            # 1. Fix methodology_data
            print("\nChecking 'methodology_data' table...")
            
            # Check if table exists
            table_exists = connection.execute(text("SELECT to_regclass('public.methodology_data')")).scalar()
            
            if not table_exists:
                print("  - Table missing. Creating...")
                connection.execute(text("""
                    CREATE TABLE methodology_data (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        paper_id TEXT NOT NULL,
                        methodology_description TEXT,
                        methodology_context TEXT,
                        approach_novelty TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(user_id, project_id, paper_id)
                    )
                """))
            else:
                print("  - Table exists. Checking columns...")
                
                # Check for typo column
                typo_col = connection.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'methodology_data' AND column_name = 'methodology_descriptiion'
                """)).scalar()
                
                if typo_col:
                    print("  - Found typo column 'methodology_descriptiion'. Renaming...")
                    connection.execute(text("ALTER TABLE methodology_data RENAME COLUMN methodology_descriptiion TO methodology_description"))
                
                # Ensure correct columns exist
                required_columns = [
                    'methodology_description',
                    'methodology_context', 
                    'approach_novelty'
                ]
                
                for col in required_columns:
                    col_exists = connection.execute(text(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'methodology_data' AND column_name = '{col}'
                    """)).scalar()
                    
                    if not col_exists:
                        print(f"  - Column '{col}' missing. Adding...")
                        connection.execute(text(f"ALTER TABLE methodology_data ADD COLUMN {col} TEXT"))
            
            # 2. Fix findings
            print("\nChecking 'findings' table...")
            
            # Check if table exists
            table_exists = connection.execute(text("SELECT to_regclass('public.findings')")).scalar()
            
            if not table_exists:
                print("  - Table missing. Creating...")
                connection.execute(text("""
                    CREATE TABLE findings (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        paper_id TEXT NOT NULL,
                        key_finding TEXT,
                        limitations TEXT,
                        custom_notes TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(user_id, project_id, paper_id)
                    )
                """))
            else:
                print("  - Table exists. Checking columns...")
                required_columns = ['key_finding', 'limitations', 'custom_notes']
                
                for col in required_columns:
                    col_exists = connection.execute(text(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'findings' AND column_name = '{col}'
                    """)).scalar()
                    
                    if not col_exists:
                        print(f"  - Column '{col}' missing. Adding...")
                        connection.execute(text(f"ALTER TABLE findings ADD COLUMN {col} TEXT"))

            connection.commit()
            print("\n✅ Schema Fix Complete!")
            
    except Exception as e:
        print(f"\n❌ Schema Repair Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_schema()
