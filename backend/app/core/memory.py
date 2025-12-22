"""
Conversation Memory Management
Stores messages in PostgreSQL 'agent_messages' table
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional
import json

class ConversationMemory:
    """Persistent conversation memory"""
    
    def __init__(self, db: Session, conversation_id: str):
        self.db = db
        self.conversation_id = conversation_id
    
    async def add_message(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict] = None
    ):
        """Add message to history"""
        self.db.execute(
            text("""
                INSERT INTO agent_messages (conversation_id, role, content, metadata)
                VALUES (:conv_id, :role, :content, :metadata)
            """),
            {
                'conv_id': self.conversation_id,
                'role': role,
                'content': content,
                'metadata': json.dumps(metadata) if metadata else None
            }
        )
        self.db.commit()
    
    async def get_history(self, last_n: int = 10) -> List[Dict]:
        """Get recent message history"""
        result = self.db.execute(
            text("""
                SELECT role, content, created_at 
                FROM agent_messages
                WHERE conversation_id = :conv_id
                ORDER BY created_at ASC
            """), # Fetch all then slice usually better for chat context window logic, 
                  # but limiting DB fetch is good optimization.
                  # Re-ordering for context: oldest first.
            {'conv_id': self.conversation_id}
        )
        
        messages = [
            {'role': row.role, 'content': row.content}
            for row in result.fetchall()
        ]
        
        # Return last N messages
        return messages[-last_n:] if last_n else messages
