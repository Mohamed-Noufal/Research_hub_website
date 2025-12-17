"""
Drop incorrect tables and apply correct migrations (without FK constraints)
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

def fix_schema():
    print("Fixing database schema...")
    print("="*70)
    
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    try:
        # Step 1: Drop incorrect tables
        print("\n1. Dropping incorrect tables...")
        drop_sql = """
        DROP TABLE IF EXISTS comparison_configs CASCADE;
        DROP TABLE IF EXISTS comparison_attributes CASCADE;
        DROP TABLE IF EXISTS synthesis_configs CASCADE;
        DROP TABLE IF EXISTS synthesis_cells CASCADE;
        DROP TABLE IF EXISTS analysis_configs CASCADE;
        """
        conn.execute(text(drop_sql))
        conn.commit()
        print("✅ Old tables dropped")
        
        # Step 2: Create tables with correct schema (without FK constraints)
        print("\n2. Creating tables with correct schema...")
        
        # Comparison tables
        print("\n   Creating comparison_configs...")
        conn.execute(text("""
        CREATE TABLE comparison_configs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            project_id INTEGER NOT NULL,
            
            selected_paper_ids TEXT[] NOT NULL DEFAULT '{}',
            insights_similarities TEXT,
            insights_differences TEXT,
            
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, project_id)
        );
        CREATE INDEX idx_comparison_configs_project ON comparison_configs(project_id, user_id);
        """))
        conn.commit()
        print("   ✅ comparison_configs created")
        
        print("\n   Creating comparison_attributes...")
        conn.execute(text("""
        CREATE TABLE comparison_attributes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            project_id INTEGER NOT NULL,
            paper_id INTEGER NOT NULL,
            
            attribute_name VARCHAR(100) NOT NULL,
            attribute_value TEXT,
            
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, project_id, paper_id, attribute_name)
        );
        CREATE INDEX idx_comparison_attributes_project ON comparison_attributes(project_id, user_id);
        """))
        conn.commit()
        print("   ✅ comparison_attributes created")
        
        # Synthesis tables
        print("\n   Creating synthesis_configs...")
        conn.execute(text("""
        CREATE TABLE synthesis_configs (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL,
            project_id INTEGER NOT NULL,
            
            columns JSONB NOT NULL DEFAULT '[]',
            rows JSONB NOT NULL DEFAULT '[]',
            
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, project_id)
        );
        CREATE INDEX idx_synthesis_configs_project ON synthesis_configs(project_id, user_id);
        """))
        conn.commit()
        print("   ✅ synthesis_configs created")
        
        print("\n   Creating synthesis_cells...")
        conn.execute(text("""
        CREATE TABLE synthesis_cells (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL,
            project_id INTEGER NOT NULL,
            
            row_id VARCHAR(100) NOT NULL,
            column_id VARCHAR(100) NOT NULL,
            value TEXT,
            
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, project_id, row_id, column_id)
        );
        CREATE INDEX idx_synthesis_cells_project ON synthesis_cells(project_id, user_id);
        """))
        conn.commit()
        print("   ✅ synthesis_cells created")
        
        # Analysis tables
        print("\n   Creating analysis_configs...")
        conn.execute(text("""
        CREATE TABLE analysis_configs (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL,
            project_id INTEGER NOT NULL,
            
            chart_preferences JSONB DEFAULT '{}',
            custom_metrics JSONB DEFAULT '[]',
            
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, project_id)
        );
        CREATE INDEX idx_analysis_configs_project ON analysis_configs(project_id, user_id);
        """))
        conn.commit()
        print("   ✅ analysis_configs created")
        
        print("\n" + "="*70)
        print("✅ Schema fixed successfully!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_schema()
    sys.exit(0 if success else 1)
