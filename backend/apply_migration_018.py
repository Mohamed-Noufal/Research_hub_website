"""
Apply migration 018 to fix research_gaps table schema
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Read migration file
with open('migrations/018_fix_project_references.sql', 'r') as f:
    migration_sql = f.read()

# Connect to database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/research_hub')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("🔄 Applying migration 018_fix_project_references.sql...")
    
    # Execute migration
    cur.execute(migration_sql)
    conn.commit()
    
    print("✅ Migration applied successfully!")
    
    # Verify research_gaps table structure
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'research_gaps'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    print("\n📋 research_gaps table columns:")
    for col_name, col_type in columns:
        print(f"  - {col_name}: {col_type}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
