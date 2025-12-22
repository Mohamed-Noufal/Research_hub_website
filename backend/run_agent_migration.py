"""
Run migration 020_agent_system.sql to create AI agent tables
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def run_migration():
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env file")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print("📊 Running migration 020_agent_system.sql...")
        
        # Read and execute migration
        with open('migrations/020_agent_system.sql', 'r') as f:
            migration_sql = f.read()
            cur.execute(migration_sql)
        
        conn.commit()
        
        # Verify tables were created
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'paper_chunks', 
                'agent_conversations', 
                'agent_messages', 
                'agent_tool_calls',
                'llm_usage_logs',
                'rag_usage_logs'
            )
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        
        print("\n✅ Migration completed successfully!")
        print(f"📋 Created/verified {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Verify pgvector extension
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
        vector_ext = cur.fetchone()
        if vector_ext:
            print(f"\n✅ pgvector extension enabled (version {vector_ext[2]})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
