
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.core.config import settings

def apply_migration():
    print("🚀 Applying migration 021_advanced_rag.sql...")
    
    # Get absolute path to migrations dir
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, "migrations", "021_advanced_rag.sql")
    
    # Read sql file
    with open(sql_path, "r") as f:
        sql = f.read()
        
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Execute
            conn.execute(text(sql))
            conn.commit()
            print("✅ Migration 021 applied successfully!")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            
if __name__ == "__main__":
    apply_migration()
