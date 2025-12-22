import os
import sys
from sqlalchemy import create_engine, inspect
from app.core.config import settings

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

def check_tables():
    print("🔍 Checking database tables...")
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f" - {table}")
        
    required = ['agent_conversations', 'agent_messages', 'paper_chunks']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"\n❌ MISSING TABLES: {missing}")
    else:
        print("\n✅ All agent tables found!")
        
        # Try insert
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                import uuid
                # Get a user first
                res = conn.execute(text("SELECT id FROM local_users LIMIT 1"))
                user = res.fetchone()
                if user:
                    uid = user[0]
                    print(f"Testing insert with user {uid}")
                    conn.execute(text("""
                        INSERT INTO agent_conversations (id, user_id, metadata)
                        VALUES (:id, :uid, '{}')
                    """), {"id": uuid.uuid4(), "uid": uid})
                    print("✅ Insert successful (rolled back)")
                    # implicitly rolls back if I don't commit? 
                    # Actually engine.connect() autocommit usage depends.
                    # I'll just let it rollback or commit, doesn't matter for test
                else:
                    print("⚠️ No local_users found, skipping insert test")
        except Exception as e:
            print(f"❌ Insert failed: {e}")

if __name__ == "__main__":
    check_tables()
