import asyncio
import os
from app.core.rag_engine import RAGEngine
from app.core.llm_client import LLMClient
from app.agents.base import FlexibleAgent, Tool
from app.core.memory import ConversationMemory
from app.core.database import get_db

async def test_phase2_components():
    print("=" * 60)
    print("🧪 Phase 2 Verification Test")
    print("=" * 60)
    
    # 1. Test LLM Client
    print("\n1️⃣ Testing LLM Client...")
    try:
        # Dummy DB session
        db_gen = get_db()
        db = next(db_gen)
        client = LLMClient(db)
        print("   ✓ LLM Client initialized")
    except Exception as e:
        print(f"   ❌ LLM Client failed: {e}")

    # 2. Test RAG Engine
    print("\n2️⃣ Testing RAG Engine...")
    try:
        # Check env vars first
        if not os.getenv("DATABASE_URL"):
            print("   ⚠️ DATABASE_URL missing, skipping RAG init")
        else:
            rag = RAGEngine()
            print("   ✓ RAG Engine initialized")
            print(f"   ✓ Index ready: {rag.index is not None}")
    except Exception as e:
        print(f"   ❌ RAG Engine failed: {e}")

    # 3. Test Agent Framework
    print("\n3️⃣ Testing Flexible Agent...")
    try:
        tools = [
            Tool(
                name="test_tool",
                description="A test tool",
                parameters={"input": "str"},
                function=lambda x: f"Echo: {x}"
            )
        ]
        agent = FlexibleAgent("TestAgent", client, tools)
        print(f"   ✓ Agent initialized with {len(agent.tools)} tools")
    except Exception as e:
        print(f"   ❌ Agent framework failed: {e}")

    print("\n" + "=" * 60)
    print("✅ Phase 2 Verification Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_phase2_components())
