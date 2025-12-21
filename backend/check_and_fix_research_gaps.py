"""
Check research_gaps table structure
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/research_hub')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check if research_gaps table exists and its structure
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'research_gaps'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    
    if columns:
        print("✅ research_gaps table exists with columns:")
        for col_name, col_type, nullable in columns:
            print(f"  - {col_name}: {col_type} (nullable: {nullable})")
        
        # Check if 'notes' column exists
        has_notes = any(col[0] == 'notes' for col in columns)
        if has_notes:
            print("\n✅ 'notes' column EXISTS - migration successful!")
        else:
            print("\n❌ 'notes' column MISSING - need to add it")
            
            # Add notes column if missing
            print("\n🔧 Adding 'notes' column...")
            cur.execute("""
                ALTER TABLE research_gaps 
                ADD COLUMN IF NOT EXISTS notes TEXT;
            """)
            conn.commit()
            print("✅ 'notes' column added successfully!")
    else:
        print("❌ research_gaps table does not exist!")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
