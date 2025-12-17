
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_schema():
    print("🔌 Connecting to database...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("🛠️ Checking and fixing comparison_configs table...")
        
        # Add selected_attributes if not exists
        try:
            conn.execute(text("""
                ALTER TABLE comparison_configs 
                ADD COLUMN IF NOT EXISTS selected_attributes JSONB DEFAULT '{}'::jsonb
            """))
            print("✅ Added/Verified column: selected_attributes")
        except Exception as e:
            print(f"❌ Error adding selected_attributes: {e}")

        # Add view_mode if not exists
        try:
            conn.execute(text("""
                ALTER TABLE comparison_configs 
                ADD COLUMN IF NOT EXISTS view_mode VARCHAR DEFAULT 'table'
            """))
            print("✅ Added/Verified column: view_mode")
        except Exception as e:
            print(f"❌ Error adding view_mode: {e}")
            
        conn.commit()
        print("✨ Schema update completed!")

if __name__ == "__main__":
    # Add parent directory to path to import app modules
    sys.path.append(os.getcwd())
    fix_schema()
