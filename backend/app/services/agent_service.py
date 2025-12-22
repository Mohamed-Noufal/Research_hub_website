"""
Agent Service
Handles AI assistant conversations, message processing, and tool orchestration
"""
from typing import List, Dict, Optional, Any, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal
from app.agents.orchestrator import OrchestratorAgent
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
import uuid
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class AgentService:
    """
    Service for managing AI Assistant conversations and execution
    """
    
    _instance = None
    _orchestrator = None
    
    def __init__(self):
        # Singleton orchestrator init to avoid reloading models
        if not AgentService._orchestrator:
            try:
                db = SessionLocal()
                llm = LLMClient(db)
                # RAG is lazy-loaded only when tools need it (prevents 60s startup delay)
                rag = None  
                AgentService._orchestrator = OrchestratorAgent(llm, db, rag)
                logger.info("✅ Orchestrator Agent initialized in Service (RAG will load on first use)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Orchestrator: {e}")
                # We don't raise here to allow API to start, but agent endpoints will fail
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    async def create_conversation(
        self, 
        user_id: str, 
        title: Optional[str] = "New Conversation",
        project_id: Optional[int] = None
    ) -> str:
        """Create a new conversation"""
        db = SessionLocal()
        try:
            conv_id = str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO agent_conversations (id, user_id, project_id, metadata)
                    VALUES (:id, :user_id, :project_id, :metadata)
                """),
                {
                    'id': conv_id, 
                    'user_id': user_id, 
                    'project_id': project_id,
                    'metadata': json.dumps({"title": title})
                }
            )
            db.commit()
            return conv_id
        finally:
            db.close()

    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict]:
        """Get message history for a conversation"""
        db = SessionLocal()
        try:
            result = db.execute(
                text("""
                    SELECT role, content, created_at, metadata
                    FROM agent_messages
                    WHERE conversation_id = :conv_id
                    ORDER BY created_at ASC
                """),
                {'conv_id': conversation_id}
            )
            
            messages = []
            for row in result.fetchall():
                msg = {
                    'role': row.role,
                    'content': row.content,
                    'created_at': row.created_at.isoformat(),
                    'metadata': json.loads(row.metadata) if row.metadata else {}
                }
                messages.append(msg)
            return messages
        finally:
            db.close()

    async def process_message(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        project_id: Optional[int] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Process a user message and stream updates/response
        Using generator to support WebSocket streaming of "Thinking" steps
        """
        if not self._orchestrator:
            yield {"type": "error", "content": "Agent system not initialized"}
            return

        db = SessionLocal()
        try:
            # 1. Save User Message
            db.execute(
                text("""
                    INSERT INTO agent_messages (conversation_id, role, content)
                    VALUES (:conv_id, 'user', :content)
                """),
                {'conv_id': conversation_id, 'content': message}
            )
            db.commit()
            
            # 2. Run Agent
            # Note: The Orchestrator currently returns a single result. 
            # Phase 4 enhancement: We could modify orchestrator to yield steps if we wanted streaming steps.
            # For now, we simulate "Working" state or use a simple await.
            
            yield {"type": "status", "status": "thinking", "message": "Analyzing request..."}
            
            # Update context
            if project_id:
                # Update conversation project link if provided
                db.execute(
                    text("UPDATE agent_conversations SET project_id = :pid WHERE id = :cid"),
                    {'pid': project_id, 'cid': conversation_id}
                )
                db.commit()

            # Execute Agent Logic
            # We wrap this to catch errors and log them
            try:
                response = await self._orchestrator.process_user_message(
                    user_id=user_id,
                    message=message,
                    project_id=project_id
                )
                
                final_answer = response.get('result', "I'm sorry, I couldn't process that request.")
                steps_count = response.get('steps', 0)
                
                # 3. Save Assistant Message
                db.execute(
                    text("""
                        INSERT INTO agent_messages (conversation_id, role, content, metadata)
                        VALUES (:conv_id, 'assistant', :content, :meta)
                    """),
                    {
                        'conv_id': conversation_id, 
                        'content': final_answer,
                        'meta': json.dumps({"steps": steps_count, "status": response.get('status')})
                    }
                )
                db.commit()
                
                yield {"type": "message", "role": "assistant", "content": final_answer}
                yield {"type": "message_end"}  # Signal completion to frontend
                
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                yield {"type": "error", "content": f"An error occurred: {str(e)}"}
                
        finally:
            db.close()
