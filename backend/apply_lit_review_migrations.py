"""
Apply all missing literature review migrations
"""
import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/paper_search"

def apply_migrations():
    print("Applying missing literature review migrations...")
    print("="*70)
    
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    migrations = [
        ('015_comparison_data.sql', 'Comparison Tab'),
        ('016_synthesis_data.sql', 'Synthesis Tab'),
        ('017_analysis_data.sql', 'Analysis Tab')
    ]
    
    try:
        for filename, description in migrations:
            print(f"\nApplying {filename} ({description})...")
            
            migration_path = os.path.join('migrations', filename)
            
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            # Execute the migration
            conn.execute(text(migration_sql))
            conn.commit()
            
            print(f"✅ {filename} applied successfully")
        
        print("\n" + "="*70)
        print("All migrations applied successfully!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = apply_migrations()
    sys.exit(0 if success else 1)
