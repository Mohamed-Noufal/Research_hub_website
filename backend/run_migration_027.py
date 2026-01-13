"""Run migration 027 to fix agent_task_states status column"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

try:
    # Drop old constraint
    cur.execute("ALTER TABLE agent_task_states DROP CONSTRAINT IF EXISTS agent_task_states_status_check")
    print("✓ Dropped old constraint")
    
    # Expand column size
    cur.execute("ALTER TABLE agent_task_states ALTER COLUMN status TYPE VARCHAR(30)")
    print("✓ Expanded column to VARCHAR(30)")
    
    # Add new constraint with all status values
    cur.execute("""
        ALTER TABLE agent_task_states 
        ADD CONSTRAINT agent_task_states_status_check 
        CHECK (status IN ('pending', 'running', 'completed', 'completed_with_errors', 'failed', 'paused'))
    """)
    print("✓ Added new constraint")
    
    print("\n✅ Migration 027 successful! Status column now supports 'completed_with_errors'")
except Exception as e:
    print(f"❌ Migration failed: {e}")
finally:
    cur.close()
    conn.close()
