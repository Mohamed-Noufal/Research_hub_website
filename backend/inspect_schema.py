#!/usr/bin/env python3
"""
Comprehensive Database Schema Inspector
Extracts all tables, columns, data types, and foreign key relationships
"""
import asyncio
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

async def inspect_schema():
    """Inspect database schema and document all relationships"""
    
    # Use async engine
    db_url = settings.DATABASE_URL
    if "postgresql+asyncpg" not in db_url:
        if "postgresql://" in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(db_url)
    
    print("=" * 80)
    print("DATABASE SCHEMA INSPECTION")
    print("=" * 80)
    print()
    
    async with engine.connect() as conn:
        # Get all tables
        result = await conn.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"📊 Total Tables: {len(tables)}")
        print()
        
        # Group tables by category
        core_tables = ['papers', 'paper_chunks', 'projects', 'project_papers']
        user_tables = [t for t in tables if t.startswith('user_')]
        rag_tables = ['paper_chunks', 'rag_usage_logs', 'llm_usage_logs']
        literature_tables = [t for t in tables if 'literature' in t or 'synthesis' in t]
        
        print("📁 TABLE CATEGORIES:")
        print(f"  Core Paper Management: {len(core_tables)} tables")
        print(f"  User Management: {len(user_tables)} tables")
        print(f"  RAG/AI: {len([t for t in tables if t in rag_tables])} tables")
        print(f"  Literature Review: {len([t for t in tables if t in literature_tables])} tables")
        print()
        
        # Inspect critical tables in detail
        critical_tables = ['papers', 'paper_chunks', 'projects', 'project_papers', 
                          'user_saved_papers', 'local_users', 'conversations', 
                          'user_literature_reviews']
        
        for table_name in critical_tables:
            if table_name not in tables:
                continue
                
            print("=" * 80)
            print(f"TABLE: {table_name}")
            print("=" * 80)
            
            # Get columns
            col_result = await conn.execute(text(f"""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """))
            
            print("\n📋 COLUMNS:")
            for row in col_result.fetchall():
                nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
                default = f" DEFAULT {row[3]}" if row[3] else ""
                print(f"  • {row[0]:<30} {row[1]:<20} {nullable}{default}")
            
            # Get foreign keys
            fk_result = await conn.execute(text(f"""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                  ON rc.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = '{table_name}'
            """))
            
            fks = fk_result.fetchall()
            if fks:
                print("\n🔗 FOREIGN KEYS:")
                for fk in fks:
                    print(f"  • {fk[0]} → {fk[1]}.{fk[2]} (ON DELETE {fk[3]})")
            
            # Get incoming foreign keys (what references this table)
            incoming_result = await conn.execute(text(f"""
                SELECT
                    tc.table_name,
                    kcu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND ccu.table_name = '{table_name}'
            """))
            
            incoming = incoming_result.fetchall()
            if incoming:
                print("\n⬅️  REFERENCED BY:")
                for ref in incoming:
                    print(f"  • {ref[0]}.{ref[1]}")
            
            # Get row count
            count_result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = count_result.scalar()
            print(f"\n📊 Row Count: {count:,}")
            print()
    
    await engine.dispose()
    
    print("=" * 80)
    print("🔍 KEY FINDINGS FOR RESET PLAN:")
    print("=" * 80)
    print("""
1. CASCADE IMPACT:
   - papers table is referenced by multiple tables
   - TRUNCATE papers CASCADE will affect:
     * project_papers (links papers to projects)
     * user_saved_papers (user's library)
     * user_notes (notes on papers)
     * user_annotations (highlights/annotations)
     * And potentially more tables

2. RECOMMENDATION:
   Instead of TRUNCATE CASCADE (which wipes user data too),
   we should:
   a) Delete ONLY orphaned papers (papers with no PDF file)
   b) Keep papers that have physical files
   c) Re-index existing valid papers
   d) Preserve user_saved_papers, notes, annotations

3. SAFER APPROACH:
   - Identify which paper IDs have physical files
   - Delete papers NOT in that list
   - paper_chunks will auto-delete via CASCADE
   - User data (saved papers, notes) stays intact
    """)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(inspect_schema())
