
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.api.v1.table_config import get_project_papers
from app.api.v1.users import get_current_user_id

async def diagnose():
    db = SessionLocal()
    user_id = get_current_user_id() # This is the dependency function, returns string
    print(f"Debug: Using user_id={user_id}")
    
    project_id = 9 # Use a likely project ID (from previous logs) or 1
    
    print(f"--- Diagnosing get_project_papers(project_id={project_id}) ---")
    try:
        # We need to run this in an event loop since it is async
        result = await get_project_papers(project_id=project_id, db=db, user_id=user_id)
        print("Success!")
        # print(result)
    except Exception as e:
        print("\n\n❌ CAPTURED EXCEPTION:")
        # Check if pydantic error
        if type(e).__name__ == "ValidationError":
             print(e.json())
        else:
             import traceback
             traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
