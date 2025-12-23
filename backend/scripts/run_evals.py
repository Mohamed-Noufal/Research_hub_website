import asyncio
import os
import sys
from typing import List, Dict

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


from app.core.database import SessionLocal
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.agents.orchestrator import OrchestratorAgent
from app.core.monitoring import MonitoringManager

# Dataset of questions
EVAL_QUESTIONS = [
    "What is the main contribution of the Transformer paper?",
    "Compare LSTM vs Transformer architecture.",
    "Summarize the methodology of paper ID 1."
]

async def run_evals():
    print("🚀 Starting Agent Evaluation...")
    
    # Initialize monitoring
    MonitoringManager.get_instance()
    
    db = SessionLocal()
    llm = LLMClient(db)
    rag = RAGEngine() # Assumes we have some real connection or this will fail if no DB
    
    agent = OrchestratorAgent(llm, db, rag)
    
    results = []
    
    for q in EVAL_QUESTIONS:
        print(f"\n❓ Question: {q}")
        try:
            response = await agent.process_user_message(
                user_id="eval_user",
                message=q,
                project_id=1 # assuming a test project exists
            )
            print(f"✅ Answer: {response.get('result')}")
            results.append({
                "question": q,
                "answer": response.get('result'),
                "steps": response.get('steps'),
                "status": response.get('status')
            })
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "question": q,
                "error": str(e)
            })
            
    print("\n📊 Evaluation Complete.")
    print(f"processed {len(results)} questions.")
    
if __name__ == "__main__":
    asyncio.run(run_evals())
