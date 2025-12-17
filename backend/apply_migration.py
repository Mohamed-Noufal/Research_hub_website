"""
Apply the database migration to fix paper_id type mismatches
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

def apply_migration():
    print("Applying database migration: 013_fix_paper_id_types.sql")
    print("="*70)
    
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    try:
        # Read the migration file
        migration_path = os.path.join(os.path.dirname(__file__), 'migrations', '013_fix_paper_id_types.sql')
        
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        print("\nExecuting migration...")
        
        # Execute the migration
        conn.execute(text(migration_sql))
        conn.commit()
        
        print("\n✅ Migration applied successfully!")
        
        # Verify the changes
        print("\nVerifying changes...")
        
        findings_type = conn.execute(text("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'findings' AND column_name = 'paper_id'
        """)).fetchone()
        
        methodology_type = conn.execute(text("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'methodology_data' AND column_name = 'paper_id'
        """)).fetchone()
        
        print(f"findings.paper_id type: {findings_type[0] if findings_type else 'NOT FOUND'}")
        print(f"methodology_data.paper_id type: {methodology_type[0] if methodology_type else 'NOT FOUND'}")
        
        if findings_type and methodology_type:
            if findings_type[0] == 'integer' and methodology_type[0] == 'integer':
                print("\n✅ All types converted successfully to INTEGER!")
                return True
            else:
                print("\n⚠️ Warning: Types may not have converted correctly")
                return False
        else:
            print("\n⚠️ Warning: Could not verify column types")
            return False
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
