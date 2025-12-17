"""
Run database migration for folders feature
"""
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "paper_search"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "postgres")
)

cursor = conn.cursor()

try:
    # Read and execute migration
    with open('migrations/002_add_folders.sql', 'r') as f:
        migration_sql = f.read()
    
    cursor.execute(migration_sql)
    conn.commit()
    
    print("✅ Migration completed successfully!")
    print("Created tables: folders, folder_papers")
    print("Added column: papers.is_manual")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Migration failed: {e}")
    
finally:
    cursor.close()
    conn.close()
