import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

def apply_migration():
    print("🚀 Applying migration 020_agent_system.sql...")
    
    # Read sql file
    with open("migrations/020_agent_system.sql", "r") as f:
        sql = f.read()
        
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Split by statements? Or execute whole block?
        # psycopg2 can usually handle multiple statements, but safely let's check
        try:
            conn.execute(text(sql))
            conn.commit()
            print("✅ Migration applied successfully!")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            
if __name__ == "__main__":
    apply_migration()
