import sys
import os
import uuid
from sqlalchemy import create_engine, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import settings, if fails, hardcode or error out clearly
try:
    from app.core.config import settings
except ImportError:
    # Fallback/Mock for testing if app import fails
    class Settings:
        DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/paper_search" # Adjust if known
    settings = Settings()
    print("⚠️  Could not import settings, using default/fallback URL")

# Mock get_current_user_id to avoid importing full API stack
def get_current_user_id():
    return "550e8400-e29b-41d4-a716-446655440000"

def diagnose():
    print("🔍 Starting Diagnostic Check...")
    
    # 1. Connect to DB
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    connection = engine.connect()
    
    try:
        # 2. Get User ID
        user_id_str = get_current_user_id()
        print(f"User ID from API: {user_id_str}")
        
        # 3. Create a Test Project
        print("Creating Test Project...")
        project_title = f"Diagnostic Test {uuid.uuid4().hex[:8]}"
        
        # We need to find the local_user UUID object for the INSERT if schema uses UUID
        # But wait, seed function expects user_id as string then converts. 
        # UserLiteratureReview table expects user_id as UUID object?
        # Let's verify UserLiteratureReview schema from models
        # It says: user_id = Column(UUID(as_uuid=True)...)
        
        user_uuid = uuid.UUID(user_id_str)
        
        # Ensure user exists
        check_user = connection.execute(text("SELECT id FROM local_users WHERE id = :uid"), {"uid": user_uuid}).fetchone()
        if not check_user:
            print("User does not exist, creating...")
            connection.execute(text("INSERT INTO local_users (id) VALUES (:uid)"), {"uid": user_uuid})
            connection.commit()
            
        # Create Project
        result = connection.execute(text("""
            INSERT INTO user_literature_reviews (user_id, title, description, paper_ids, status)
            VALUES (:uid, :title, 'Diagnostic Description', :pids, 'active')
            RETURNING id
        """), {"uid": user_uuid, "title": project_title, "pids": []})
        
        project_id = result.fetchone()[0]
        print(f"Created Project ID: {project_id}")
        connection.commit()
        
        # 4. Seed Project (Simulate Logic)
        print("Seeding Project...")
        
        # 4a. Papers (Ensure Paper 1 exists)
        paper_id = 1
        ensure_paper = connection.execute(text("SELECT id FROM papers WHERE id = :pid"), {"pid": paper_id}).fetchone()
        if not ensure_paper:
             print("Creating Mock Paper 1...")
             connection.execute(text("""
                INSERT INTO papers (id, title, authors, year, abstract, publication_date)
                VALUES (:pid, 'Deep Learning for Medical Diagnosis', ARRAY['Smith J', 'Doe A'], 2023, 'Abstract...', NOW())
             """), {"pid": paper_id})
             connection.commit()

        # 4b. Add to Project Papers
        print("Adding Paper 1 to Project...")
        connection.execute(text("""
            INSERT INTO project_papers (project_id, paper_id, added_by)
            VALUES (:pid, :paper_id, :uid)
            ON CONFLICT DO NOTHING
        """), {"pid": project_id, "paper_id": paper_id, "uid": str(user_uuid)}) # project_papers usually takes string user_id based on previous file views? check sync_project_papers calls
        
        # 4c. Seed Tab Data
        print("Seeding Methodology Data...")
        connection.execute(text("""
            INSERT INTO methodology_data (
                user_id, project_id, paper_id,
                methodology_description, approach_novelty
            ) VALUES (
                :uid, :pid, :paper_id_str,
                'Seeded Meth Description', 'Seeded Novelty'
            ) ON CONFLICT (user_id, project_id, paper_id) DO NOTHING
        """), {"uid": user_id_str, "pid": project_id, "paper_id_str": str(paper_id)})
        connection.commit()
        
        # 5. Run Query (The suspected problematic one)
        print("Running `get_project_papers` Query...")
        
        # Note: In table_config.py, project_id params is STR.
        query = text("""
            SELECT 
                p.id,
                p.title,
                md.methodology_description as "methodologyDescription",
                md.approach_novelty as "approachNovelty"
            FROM papers p
            INNER JOIN project_papers pp ON p.id = pp.paper_id
            LEFT JOIN methodology_data md ON (
                md.paper_id = p.id::text 
                AND md.user_id = :user_id 
                AND md.project_id = :project_id
            )
            WHERE pp.project_id = :project_id_filter
        """)
        
        # Attempt 1: As written in code (Str project_id params?)
        # table_config.py passes project_id as str to `md.project_id` check?
        # NO.
        # `AND md.project_id = :project_id`
        # params={"project_id": str(project_id)}
        
        # In SQL `WHERE pp.project_id = :project_id`
        
        results = connection.execute(query, {
            "user_id": user_id_str,
            "project_id": project_id, # Trying INT here first for correctness
            "project_id_filter": project_id
        }).fetchall()
        
        print(f"Results Count (Int ProjectID): {len(results)}")
        for row in results:
            print(f"Row: ID={row[0]} Title={row[1]} MethDesc={row[2]}")
            
        # Attempt 2: Like table_config.py (Str ProjectID)
        # Note: If md.project_id is INT and we pass Str, Postgres might implicit cast.
        # But if explicit check fails, that's it.
        try:
            print("Running Query with STR project_id (Simulating code)...")
            results_str = connection.execute(query, {
                "user_id": user_id_str,
                "project_id": str(project_id),
                "project_id_filter": project_id # The WHERE clause usually matches int column to int param, 
                                                # table_config used :project_id for both?
                                                # table_config: WHERE pp.project_id = :project_id
                                                # AND md.project_id = :project_id.
                                                # It passed str(project_id) to ONE param name :project_id.
            }).fetchall()
             
            print(f"Results Count (Str ProjectID): {len(results_str)}")
            for row in results_str:
                print(f"Row (Str): ID={row[0]} Title={row[1]} MethDesc={row[2]}")
                
        except Exception as e:
            print(f"❌ Query with STR failed: {e}")
            
    except Exception as e:
        print(f"❌ Diagnostic Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'project_id' in locals():
            print("Cleaning up...")
            # connection.execute(text("DELETE FROM user_literature_reviews WHERE id = :pid"), {"pid": project_id})
            # connection.commit()
            pass
        connection.close()

if __name__ == "__main__":
    diagnose()
