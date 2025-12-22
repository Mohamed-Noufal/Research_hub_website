import asyncio
import os
from app.tools.database_tools import get_project_by_name, get_project_papers
from app.agents.orchestrator import OrchestratorAgent
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.core.database import get_db

async def test_tools_and_agent():
    print("=" * 60)
    print("🧪 Phase 3 Verification Test")
    print("=" * 60)
    
    # 1. Test Database Tools
    print("\n1️⃣ Testing Database Tools...")
    db_gen = get_db()
    db = next(db_gen)
    
    # Needs a real user_id and project in DB to really work, 
    # but we can call it to see if it executes without syntax errors.
    # We'll use a dummy user_id.
    try:
        project = await get_project_by_name("Test Project", "test_user", db)
        print(f"   ✓ get_project_by_name executed (Result: {project})")
    except Exception as e:
        print(f"   ⚠️ get_project_by_name failed: {e}")
        
    print("   ✓ Database tools imported and callable")

    # 2. Test Orchestrator Initialization
    print("\n2️⃣ Testing Orchestrator Agent Initialization...")
    try:
        llm = LLMClient(db)
        rag = RAGEngine()
        orchestrator = OrchestratorAgent(llm, db, rag)
        print(f"   ✓ Orchestrator initialized with {len(orchestrator.tools)} tools")
        
        # Verify specific tools are present
        tool_names = [t.name for t in orchestrator.tools]
        required_tools = ['get_project_papers', 'semantic_search', 'parse_pdf', 'check_job_status']
        missing = [t for t in required_tools if t not in tool_names]
        
        if not missing:
            print("   ✓ All required tools present")
        else:
            print(f"   ❌ Missing tools: {missing}")
            
    except Exception as e:
        print(f"   ❌ Orchestrator initialization failed: {e}")

    # 3. Test RAG Tools Import
    print("\n3️⃣ Testing RAG Tools...")
    from app.tools import rag_tools
    print("   ✓ RAG tools imported successfully")

    # 4. Test Background Worker Tools
    print("\n4️⃣ Testing Background Worker Tools...")
    from app.tools import pdf_tools
    # We won't actually enqueue without Redis, but we check import
    print("   ✓ PDF tools (Worker-enabled) imported successfully")
    
    print("\n" + "=" * 60)
    print("✅ Phase 3 Verification Complete (Static Checks)")
    print("=" * 60)
    print("📌 To test fully:")
    print("   1. Ensure Redis is running")
    print("   2. Run 'arq app.workers.pdf_processors.WorkerSettings'")
    print("   3. Run this script with a valid database connection")

if __name__ == "__main__":
    asyncio.run(test_tools_and_agent())
