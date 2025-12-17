#!/usr/bin/env python3
"""
Literature Review Database Migration Runner
Executes all Literature Review migrations in the correct order
"""

import sys
import os
import psycopg2
from datetime import datetime
import logging

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db, engine
from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiteratureReviewMigrationRunner:
    def __init__(self):
        self.settings = get_settings()
        self.db = get_db()
        
    def get_connection(self):
        """Get direct database connection for migrations"""
        try:
            conn = psycopg2.connect(
                host=self.settings.POSTGRES_HOST,
                port=self.settings.POSTGRES_PORT,
                database=self.settings.POSTGRES_DB,
                user=self.settings.POSTGRES_USER,
                password=self.settings.POSTGRES_PASSWORD
            )
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def execute_migration(self, conn, migration_file, migration_name):
        """Execute a single migration file"""
        try:
            logger.info(f"🚀 Executing {migration_name}...")
            
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            with conn.cursor() as cursor:
                for statement in statements:
                    if statement and not statement.startswith('--'):
                        cursor.execute(statement)
            
            conn.commit()
            logger.info(f"✅ {migration_name} completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ {migration_name} failed: {e}")
            conn.rollback()
            return False
    
    def verify_table_exists(self, conn, table_name):
        """Check if a table exists"""
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                """, (table_name,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking table {table_name}: {e}")
            return False
    
    def check_migration_status(self, conn):
        """Check which migrations have been applied"""
        logger.info("📊 Checking current migration status...")
        
        # Check for core Literature Review tables
        tables_to_check = [
            'user_literature_reviews',
            'literature_review_annotations', 
            'literature_review_findings',
            'paper_comparisons',
            'citation_formats',
            'research_themes',
            'spreadsheet_templates',
            'spreadsheet_data',
            'ai_synthesis',
            'export_configurations',
            'analysis_templates'
        ]
        
        existing_tables = []
        for table in tables_to_check:
            if self.verify_table_exists(conn, table):
                existing_tables.append(table)
        
        logger.info(f"📋 Found {len(existing_tables)} Literature Review tables:")
        for table in existing_tables:
            logger.info(f"   ✓ {table}")
        
        missing_tables = set(tables_to_check) - set(existing_tables)
        if missing_tables:
            logger.info(f"📋 Missing {len(missing_tables)} tables:")
            for table in missing_tables:
                logger.info(f"   ❌ {table}")
        
        return existing_tables, missing_tables
    
    def run_all_migrations(self):
        """Execute all Literature Review migrations in order"""
        logger.info("🔄 Starting Literature Review Database Migration")
        logger.info("=" * 60)
        
        conn = self.get_connection()
        
        try:
            # Check current status
            existing_tables, missing_tables = self.check_migration_status(conn)
            
            if not missing_tables:
                logger.info("🎉 All Literature Review tables already exist!")
                return True
            
            # Migration files in order
            migrations = [
                ('backend/migrations/009_literature_review_core.sql', 'Phase 1: Core Features'),
                ('backend/migrations/010_lit_review_analysis.sql', 'Phase 2: Research Analysis'),
                ('backend/migrations/011_lit_review_advanced.sql', 'Phase 3: Advanced Features')
            ]
            
            logger.info(f"🚀 Starting migrations... ({len(migrations)} files)")
            logger.info("-" * 60)
            
            # Execute each migration
            for migration_file, migration_name in migrations:
                if not os.path.exists(migration_file):
                    logger.warning(f"⚠️  Migration file not found: {migration_file}")
                    continue
                
                success = self.execute_migration(conn, migration_file, migration_name)
                if not success:
                    logger.error(f"❌ Migration failed: {migration_name}")
                    return False
                
                # Brief pause between migrations
                import time
                time.sleep(0.5)
            
            # Final verification
            logger.info("-" * 60)
            logger.info("🔍 Final verification...")
            existing_tables_final, missing_tables_final = self.check_migration_status(conn)
            
            if not missing_tables_final:
                logger.info("🎉 ALL LITERATURE REVIEW MIGRATIONS COMPLETED SUCCESSFULLY!")
                logger.info("=" * 60)
                
                # Print summary
                logger.info("📋 Literature Review Database Schema Summary:")
                logger.info(f"   • Total tables: {len(existing_tables_final)}")
                logger.info(f"   • Phase 1 tables: Core annotations and findings")
                logger.info(f"   • Phase 2 tables: Research analysis and themes")
                logger.info(f"   • Phase 3 tables: AI synthesis and advanced features")
                logger.info("")
                logger.info("✅ Ready for Literature Review API endpoints!")
                
                return True
            else:
                logger.error(f"❌ Some tables still missing: {missing_tables_final}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration process failed: {e}")
            return False
        
        finally:
            conn.close()
    
    def rollback_migration(self):
        """Rollback all Literature Review migrations (use with caution)"""
        logger.warning("⚠️  ROLLBACK MODE - This will drop all Literature Review tables!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        
        if response.lower() != 'yes':
            logger.info("Rollback cancelled.")
            return
        
        conn = self.get_connection()
        
        try:
            # Rollback in reverse order
            rollback_commands = [
                "DROP TABLE IF EXISTS analysis_templates CASCADE;",
                "DROP TABLE IF EXISTS export_configurations CASCADE;", 
                "DROP TABLE IF EXISTS ai_synthesis CASCADE;",
                "DROP TABLE IF EXISTS spreadsheet_data CASCADE;",
                "DROP TABLE IF EXISTS spreadsheet_templates CASCADE;",
                "DROP TABLE IF EXISTS research_themes CASCADE;",
                "DROP TABLE IF EXISTS citation_formats CASCADE;",
                "DROP TABLE IF EXISTS paper_comparisons CASCADE;",
                "DROP TABLE IF EXISTS literature_review_findings CASCADE;",
                "DROP TABLE IF EXISTS literature_review_annotations CASCADE;",
                "ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS status;",
                "ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS review_metadata;",
                "ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS export_data;",
                "ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS ai_features_enabled;",
                "ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS advanced_analytics;",
                "ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS custom_views;"
            ]
            
            logger.info("🗑️  Executing rollback...")
            
            with conn.cursor() as cursor:
                for cmd in rollback_commands:
                    cursor.execute(cmd)
            
            conn.commit()
            logger.info("✅ Rollback completed!")
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            conn.rollback()
        finally:
            conn.close()

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        runner = LiteratureReviewMigrationRunner()
        runner.rollback_migration()
    else:
        runner = LiteratureReviewMigrationRunner()
        success = runner.run_all_migrations()
        
        if success:
            logger.info("\n🎊 Migration completed successfully!")
            logger.info("📝 Next steps:")
            logger.info("   1. Update user_service.py with Literature Review methods")
            logger.info("   2. Test the API endpoints")
            logger.info("   3. Start using Literature Review features!")
            sys.exit(0)
        else:
            logger.error("\n💥 Migration failed! Check the logs above.")
            sys.exit(1)

if __name__ == '__main__':
    main()
