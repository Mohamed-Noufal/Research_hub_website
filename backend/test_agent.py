"""
Test Agent System
Verify that the orchestrator can handle basic queries
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.agents.orchestrator import OrchestratorAgent

async def test_agent():
    print("🧪 Testing Agent System...\n")
    
    # Initialize components
    print("1️⃣ Initializing Database...")
    db = SessionLocal()
    
    print("2️⃣ Initializing LLM Client...")
    llm = LLMClient(db)
    
    print("3️⃣ Initializing RAG Engine...")
    try:
        rag = RAGEngine()
        print("✅ RAG Engine initialized")
    except Exception as e:
        print(f"⚠️ RAG Engine failed (expected if no papers indexed): {e}")
        print("   Continuing with limited functionality...")
        rag = None
    
    print("4️⃣ Initializing Orchestrator...")
    orchestrator = OrchestratorAgent(llm, db, rag)
    print("✅ Orchestrator ready\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Simple Greeting",
            "message": "Hello",
            "user_id": "test-user-123"
        },
        {
            "name": "General Question",
            "message": "What can you help me with?",
            "user_id": "test-user-123"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'='*60}")
        print(f"📝 Query: {test['message']}")
        
        try:
            result = await orchestrator.process_user_message(
                user_id=test['user_id'],
                message=test['message']
            )
            
            print(f"\n✅ Status: {result.get('status')}")
            print(f"📊 Steps: {result.get('steps')}")
            print(f"💬 Response:\n{result.get('result')}\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            import traceback
            traceback.print_exc()
    
    db.close()
    print("\n" + "="*60)
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_agent())
