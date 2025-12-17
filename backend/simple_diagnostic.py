"""
Simple diagnostic script that saves results to JSON file
"""
import sys
import os
import json
from sqlalchemy import create_engine, text
import uuid
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/paper_search"

USER_ID = "550e8400-e29b-41d4-a716-446655440000"

def test_queries():
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {"passed": 0, "failed": 0}
    }
    
    try:
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        
        # Setup
        user_uuid = uuid.UUID(USER_ID)
        
        # Create project
        result = conn.execute(text("""
            INSERT INTO user_literature_reviews (user_id, title, description, paper_ids, status)
            VALUES (:uid, :title, 'Test', '{}', 'active')
            RETURNING id
        """), {"uid": user_uuid, "title": f"Test {datetime.now().strftime('%H%M%S')}"})
        
        project_id = result.fetchone()[0]
        conn.commit()
        
        # Test queries
        queries = [
            {
                "name": "GET Comparison Config",
                "query": "SELECT * FROM comparison_configs WHERE user_id = :user_id AND project_id = :project_id",
                "params": {"user_id": USER_ID, "project_id": project_id}
            },
            {
                "name": "GET Research Gaps",
                "query": """
                    SELECT rg.id, rg.description, rg.priority
                    FROM research_gaps rg
                    WHERE rg.user_id = :user_id AND rg.project_id = :project_id
                """,
                "params": {"user_id": USER_ID, "project_id": project_id}
            },
            {
                "name": "GET Findings",
                "query": """
                    SELECT p.id as paper_id, p.title, f.key_finding
                    FROM papers p
                    LEFT JOIN findings f ON (f.paper_id = p.id::text AND f.user_id = :user_id AND f.project_id = :project_id)
                    WHERE p.id IN (SELECT paper_id::uuid FROM project_papers WHERE project_id = :project_id)
                    LIMIT 5
                """,
                "params": {"user_id": USER_ID, "project_id": project_id}
            },
            {
                "name": "GET Methodology Data",
                "query": """
                    SELECT p.id, p.title, md.methodology_description
                    FROM papers p
                    LEFT JOIN methodology_data md ON (md.paper_id = p.id::text AND md.user_id = :user_id AND md.project_id = :project_id)
                    WHERE p.id IN (SELECT paper_id::uuid FROM project_papers WHERE project_id = :project_id)
                    LIMIT 5
                """,
                "params": {"user_id": USER_ID, "project_id": project_id}
            },
            {
                "name": "GET Synthesis Config",
                "query": "SELECT * FROM synthesis_configs WHERE user_id = :user_id AND project_id = :project_id",
                "params": {"user_id": USER_ID, "project_id": project_id}
            },
            {
                "name": "GET Analysis Config",
                "query": "SELECT * FROM analysis_configs WHERE user_id = :user_id AND project_id = :project_id",
                "params": {"user_id": USER_ID, "project_id": project_id}
            },
            {
                "name": "GET Table Config",
                "query": "SELECT * FROM table_configs WHERE user_id = :user_id AND project_id = :project_id AND tab_name = 'library'",
                "params": {"user_id": USER_ID, "project_id": project_id}
            }
        ]
        
        for q in queries:
            test_result = {
                "name": q["name"],
                "status": "unknown",
                "error": None,
                "rows_returned": 0
            }
            
            try:
                rows = conn.execute(text(q["query"]), q["params"]).fetchall()
                test_result["status"] = "passed"
                test_result["rows_returned"] = len(rows)
                results["summary"]["passed"] += 1
            except Exception as e:
                test_result["status"] = "failed"
                test_result["error"] = str(e)
                results["summary"]["failed"] += 1
            
            results["tests"].append(test_result)
        
        # Cleanup
        conn.execute(text("DELETE FROM user_literature_reviews WHERE id = :pid"), {"pid": project_id})
        conn.commit()
        conn.close()
        
    except Exception as e:
        results["setup_error"] = str(e)
    
    # Save to JSON
    with open("diagnostic_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Tests completed: {results['summary']['passed']} passed, {results['summary']['failed']} failed")
    print("Results saved to diagnostic_results.json")
    
    return results["summary"]["failed"] == 0

if __name__ == "__main__":
    success = test_queries()
    sys.exit(0 if success else 1)
