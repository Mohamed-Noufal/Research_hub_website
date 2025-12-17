"""
Direct Database Testing for Literature Review Endpoints
Tests the SQL queries used by literature review endpoints directly against the database
to identify issues without needing the server running.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    print("⚠️  Could not import settings, using default URL")
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/paper_search"

# Simple output functions without colors
def print_success(msg):
    print(f"[SUCCESS] {msg}")

def print_error(msg):
    print(f"[ERROR] {msg}")

def print_warning(msg):
    print(f"[WARNING] {msg}")

def print_info(msg):
    print(f"[INFO] {msg}")

def print_header(msg):
    print(f"\n{'='*70}")
    print(f"{msg}")
    print(f"{'='*70}\n")


class DatabaseTester:
    def __init__(self):
        self.engine = None
        self.connection = None
        self.user_id = "550e8400-e29b-41d4-a716-446655440000"
        self.project_id = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def connect(self):
        """Connect to database"""
        try:
            print_info(f"Connecting to: {DATABASE_URL}")
            self.engine = create_engine(DATABASE_URL)
            self.connection = self.engine.connect()
            print_success("Database connected successfully")
            return True
        except Exception as e:
            print_error(f"Failed to connect to database: {e}")
            return False
    
    def test_query(self, name: str, query: str, params: dict, description: str = ""):
        """Test a SQL query"""
        try:
            print_info(f"Testing: {name}")
            if description:
                print(f"  Description: {description}")
            
            result = self.connection.execute(text(query), params)
            rows = result.fetchall()
            
            print_success(f"{name} - Query executed successfully")
            print(f"  Rows returned: {len(rows)}")
            if rows:
                print(f"  Sample row: {dict(rows[0]._mapping) if hasattr(rows[0], '_mapping') else rows[0]}")
            
            self.test_results["passed"] += 1
            return rows
            
        except Exception as e:
            print_error(f"{name} - Query failed")
            print_error(f"  Error: {str(e)}")
            print_error(f"  Query: {query[:200]}...")
            print_error(f"  Params: {params}")
            
            self.test_results["failed"] += 1
            self.test_results["errors"].append({
                "name": name,
                "error": str(e),
                "query": query,
                "params": params
            })
            return None
    
    def setup_test_data(self):
        """Create test project and data"""
        print_header("SETUP: Creating Test Data")
        
        try:
            # Ensure user exists
            user_uuid = uuid.UUID(self.user_id)
            check_user = self.connection.execute(
                text("SELECT id FROM local_users WHERE id = :uid"),
                {"uid": user_uuid}
            ).fetchone()
            
            if not check_user:
                print_info("Creating test user...")
                self.connection.execute(
                    text("INSERT INTO local_users (id) VALUES (:uid)"),
                    {"uid": user_uuid}
                )
                self.connection.commit()
                print_success("Test user created")
            
            # Create test project
            print_info("Creating test project...")
            result = self.connection.execute(text("""
                INSERT INTO user_literature_reviews (user_id, title, description, paper_ids, status)
                VALUES (:uid, :title, :desc, :pids, 'active')
                RETURNING id
            """), {
                "uid": user_uuid,
                "title": f"DB Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "desc": "Database diagnostic test",
                "pids": []
            })
            
            self.project_id = result.fetchone()[0]
            self.connection.commit()
            print_success(f"Test project created with ID: {self.project_id}")
            
            # Create test paper if doesn't exist
            paper_check = self.connection.execute(
                text("SELECT id FROM papers WHERE id = 1")
            ).fetchone()
            
            if not paper_check:
                print_info("Creating test paper...")
                self.connection.execute(text("""
                    INSERT INTO papers (id, title, authors, year, abstract, publication_date)
                    VALUES (1, 'Test Paper for Diagnostics', ARRAY['Test Author'], 2024, 
                            'Test abstract', NOW())
                """))
                self.connection.commit()
                print_success("Test paper created")
            
            # Add paper to project
            print_info("Adding paper to project...")
            self.connection.execute(text("""
                INSERT INTO project_papers (project_id, paper_id, added_by)
                VALUES (:pid, :paper_id, :uid)
                ON CONFLICT DO NOTHING
            """), {
                "pid": self.project_id,
                "paper_id": 1,
                "uid": self.user_id
            })
            self.connection.commit()
            print_success("Paper added to project")
            
            return True
            
        except Exception as e:
            print_error(f"Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_comparison_queries(self):
        """Test comparison endpoint queries"""
        print_header("TESTING: Comparison Queries")
        
        # GET comparison config
        self.test_query(
            "GET Comparison Config",
            """
            SELECT selected_paper_ids, insights_similarities, insights_differences
            FROM comparison_configs
            WHERE user_id = :user_id AND project_id = :project_id
            """,
            {"user_id": self.user_id, "project_id": self.project_id},
            "Fetch comparison configuration"
        )
        
        # INSERT comparison config
        self.test_query(
            "INSERT Comparison Config",
            """
            INSERT INTO comparison_configs (
                user_id, project_id, selected_paper_ids, 
                insights_similarities, insights_differences
            ) VALUES (
                :user_id, :project_id, :selected_paper_ids,
                :insights_similarities, :insights_differences
            )
            ON CONFLICT (user_id, project_id) DO UPDATE
            SET selected_paper_ids = EXCLUDED.selected_paper_ids
            """,
            {
                "user_id": self.user_id,
                "project_id": self.project_id,
                "selected_paper_ids": [1],
                "insights_similarities": "Test similarities",
                "insights_differences": "Test differences"
            },
            "Insert/update comparison config"
        )
        self.connection.commit()
        
        # GET comparison attributes
        self.test_query(
            "GET Comparison Attributes",
            """
            SELECT paper_id, attribute_name, attribute_value
            FROM comparison_attributes
            WHERE user_id = :user_id AND project_id = :project_id
            ORDER BY attribute_name, paper_id
            """,
            {"user_id": self.user_id, "project_id": self.project_id},
            "Fetch comparison attributes"
        )
    
    def test_findings_queries(self):
        """Test findings & gaps endpoint queries"""
        print_header("TESTING: Findings & Gaps Queries")
        
        # GET research gaps
        self.test_query(
            "GET Research Gaps",
            """
            SELECT 
                rg.id,
                rg.description,
                rg.priority,
                rg.notes,
                COALESCE(
                    json_agg(gpa.paper_id) FILTER (WHERE gpa.paper_id IS NOT NULL),
                    '[]'::json
                ) as related_paper_ids
            FROM research_gaps rg
            LEFT JOIN gap_paper_associations gpa ON gpa.gap_id = rg.id
            WHERE rg.user_id = :user_id AND rg.project_id = :project_id
            GROUP BY rg.id, rg.description, rg.priority, rg.notes
            ORDER BY 
                CASE rg.priority 
                    WHEN 'High' THEN 1 
                    WHEN 'Medium' THEN 2 
                    WHEN 'Low' THEN 3 
                END,
                rg.created_at DESC
            """,
            {"user_id": self.user_id, "project_id": self.project_id},
            "Fetch research gaps with aggregated paper associations"
        )
        
        # GET findings (THE PROBLEMATIC QUERY)
        self.test_query(
            "GET Findings",
            """
            SELECT 
                p.id as paper_id,
                p.title,
                f.key_finding,
                f.limitations
            FROM papers p
            LEFT JOIN findings f ON (
                f.paper_id = p.id::text 
                AND f.user_id = :user_id 
                AND f.project_id = :project_id
            )
            WHERE p.id IN (
                SELECT paper_id::uuid 
                FROM project_papers 
                WHERE project_id = :project_id
            )
            ORDER BY p.year DESC, p.title
            """,
            {"user_id": self.user_id, "project_id": self.project_id},
            "Fetch findings for all papers in project"
        )
    
    def test_methodology_queries(self):
        """Test methodology endpoint queries"""
        print_header("TESTING: Methodology Queries")
        
        # GET methodology data (THE PROBLEMATIC QUERY)
        self.test_query(
            "GET Methodology Data",
            """
            SELECT 
                p.id as paper_id,
                p.title,
                p.methodology,
                p.methodology_type,
                md.methodology_description,
                md.methodology_context,
                md.approach_novelty,
                md.custom_attributes
            FROM papers p
            LEFT JOIN methodology_data md ON (
                md.paper_id = p.id::text 
                AND md.user_id = :user_id 
                AND md.project_id = :project_id
            )
            WHERE p.id IN (
                SELECT paper_id::uuid 
                FROM project_papers 
                WHERE project_id = :project_id
            )
            ORDER BY p.year DESC, p.title
            """,
            {"user_id": self.user_id, "project_id": self.project_id},
            "Fetch methodology data for all papers in project"
        )
    
    def test_synthesis_queries(self):
        """Test synthesis endpoint queries"""
        print_header("TESTING: Synthesis Queries")
        
        # GET synthesis structure
        self.test_query(
            "GET Synthesis Structure",
            """
            SELECT columns, rows
            FROM synthesis_configs
            WHERE user_id = :user_id AND project_id = :project_id
            """,
            {"user_id": self.user_id, "project_id": self.project_id},
            "Fetch synthesis table structure"
        )
        
        # GET synthesis cells
        self.test_query(
            "GET Synthesis Cells",
            """
            SELECT row_id, column_id, value
            FROM synthesis_cells
            WHERE user_id = :user_id AND project_id = :project_id
            """,
            {"user_id": self.user_id, "project_id": self.project_id},
            "Fetch synthesis cell values"
        )
    
    def test_analysis_queries(self):
        """Test analysis endpoint queries"""
        print_header("TESTING: Analysis Queries")
        
        # GET analysis config
        self.test_query(
            "GET Analysis Config",
            """
            SELECT chart_preferences, custom_metrics
            FROM analysis_configs
            WHERE user_id = :user_id AND project_id = :project_id
            """,
            {"user_id": self.user_id, "project_id": self.project_id},
            "Fetch analysis configuration"
        )
    
    def test_table_config_queries(self):
        """Test table config endpoint queries"""
        print_header("TESTING: Table Config Queries")
        
        # GET table config
        self.test_query(
            "GET Table Config",
            """
            SELECT visible_columns, column_order, custom_fields
            FROM table_configs
            WHERE user_id = :user_id AND project_id = :project_id AND tab_name = :tab_name
            """,
            {"user_id": self.user_id, "project_id": self.project_id, "tab_name": "library"},
            "Fetch table configuration"
        )
        
        # GET project papers (THE MOST PROBLEMATIC QUERY)
        self.test_query(
            "GET Project Papers",
            """
            SELECT 
                p.id,
                p.title,
                md.methodology_description as \"methodologyDescription\",
                md.approach_novelty as \"approachNovelty\"
            FROM papers p
            INNER JOIN project_papers pp ON p.id = pp.paper_id
            LEFT JOIN methodology_data md ON (
                md.paper_id = p.id::text 
                AND md.user_id = :user_id 
                AND md.project_id = :project_id
            )
            WHERE pp.project_id = :project_id
            """,
            {"user_id": self.user_id, "project_id": self.project_id},
            "Fetch all papers in project with methodology data"
        )
    
    def cleanup(self):
        """Clean up test data"""
        print_header("CLEANUP: Removing Test Data")
        
        if self.project_id:
            try:
                # Delete project (cascade should handle related data)
                self.connection.execute(
                    text("DELETE FROM user_literature_reviews WHERE id = :pid"),
                    {"pid": self.project_id}
                )
                self.connection.commit()
                print_success("Test project deleted")
            except Exception as e:
                print_warning(f"Cleanup warning: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total = self.test_results["passed"] + self.test_results["failed"]
        print(f"Total Queries Tested: {total}")
        print_success(f"Passed: {self.test_results['passed']}")
        print_error(f"Failed: {self.test_results['failed']}")
        
        if self.test_results["errors"]:
            print_header("ERRORS DETAIL")
            for i, error in enumerate(self.test_results["errors"], 1):
                print(f"\n[ERROR {i}]: {error['name']}")
                print(f"  Error: {error['error']}")
                print(f"  Query: {error['query'][:200]}...")
                print(f"  Params: {error['params']}")
        
        return self.test_results["failed"] == 0
    
    def run_all_tests(self):
        """Run all database tests"""
        print_header("LITERATURE REVIEW DATABASE DIAGNOSTIC")
        
        if not self.connect():
            return False
        
        try:
            if not self.setup_test_data():
                return False
            
            # Run all query tests
            self.test_comparison_queries()
            self.test_findings_queries()
            self.test_methodology_queries()
            self.test_synthesis_queries()
            self.test_analysis_queries()
            self.test_table_config_queries()
            
            # Cleanup
            self.cleanup()
            
            # Summary
            return self.print_summary()
            
        finally:
            if self.connection:
                self.connection.close()
                print_info("Database connection closed")


def main():
    """Main test runner"""
    tester = DatabaseTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
