"""Verify and run migration 025"""
from sqlalchemy import text
from app.core.database import SessionLocal

def check_tables():
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('paper_sections', 'paper_figures', 'paper_tables', 'paper_equations', 'project_summaries')
            AND table_schema = 'public'
        """))
        existing = [r[0] for r in result.fetchall()]
        print(f"Existing tables: {existing}")
        
        needed = {'paper_sections', 'paper_figures', 'paper_tables', 'paper_equations', 'project_summaries'}
        missing = needed - set(existing)
        
        if missing:
            print(f"Missing tables: {missing}")
            return False
        else:
            print("✅ All tables exist!")
            return True
    finally:
        db.close()

def run_migration():
    db = SessionLocal()
    try:
        statements = [
            # paper_sections
            """CREATE TABLE IF NOT EXISTS paper_sections (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
                user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
                section_type VARCHAR(50) NOT NULL,
                section_title VARCHAR(500),
                content TEXT NOT NULL,
                word_count INTEGER,
                order_index INTEGER DEFAULT 0,
                page_start INTEGER,
                page_end INTEGER,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )""",
            
            # paper_figures
            """CREATE TABLE IF NOT EXISTS paper_figures (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
                user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
                figure_number VARCHAR(50),
                caption TEXT,
                image_path VARCHAR(1000),
                image_url VARCHAR(1000),
                page_number INTEGER,
                order_index INTEGER DEFAULT 0,
                width INTEGER,
                height INTEGER,
                format VARCHAR(20),
                embedding vector(768),
                created_at TIMESTAMP DEFAULT NOW()
            )""",
            
            # paper_tables
            """CREATE TABLE IF NOT EXISTS paper_tables (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
                user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
                table_number VARCHAR(50),
                caption TEXT,
                content_markdown TEXT,
                content_json JSONB,
                page_number INTEGER,
                order_index INTEGER DEFAULT 0,
                row_count INTEGER,
                column_count INTEGER,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT NOW()
            )""",
            
            # paper_equations
            """CREATE TABLE IF NOT EXISTS paper_equations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
                user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
                equation_number VARCHAR(50),
                latex TEXT NOT NULL,
                mathml TEXT,
                context TEXT,
                page_number INTEGER,
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )""",
            
            # project_summaries
            """CREATE TABLE IF NOT EXISTS project_summaries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
                summary_text TEXT,
                key_insights TEXT[],
                methodology_overview TEXT,
                main_findings TEXT,
                research_gaps TEXT[],
                future_directions TEXT,
                word_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(project_id, user_id)
            )"""
        ]
        
        for stmt in statements:
            try:
                db.execute(text(stmt))
                db.commit()
                print(f"✓ Created table")
            except Exception as e:
                db.rollback()
                if "already exists" in str(e).lower():
                    print(f"⚠ Table already exists")
                else:
                    print(f"Error: {e}")
        
        # Add columns to papers
        alter_statements = [
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP",
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP",
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS processing_error TEXT",
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS section_count INTEGER DEFAULT 0",
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS figure_count INTEGER DEFAULT 0",
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS table_count INTEGER DEFAULT 0",
            "ALTER TABLE papers ADD COLUMN IF NOT EXISTS equation_count INTEGER DEFAULT 0"
        ]
        
        for stmt in alter_statements:
            try:
                db.execute(text(stmt))
                db.commit()
                print(f"✓ Column added")
            except Exception as e:
                db.rollback()
                print(f"⚠ Column may exist: {str(e)[:50]}")
        
        print("\n✅ Migration complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    if not check_tables():
        run_migration()
        check_tables()
    else:
        print("No migration needed")
