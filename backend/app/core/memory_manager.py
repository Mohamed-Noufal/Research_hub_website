"""
Memory Manager - Mem0-inspired long-term memory system
Extracts, stores, and retrieves user memories across conversations.
"""
from typing import List, Dict, Optional, Any
from sqlalchemy import text
import json
import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Mem0-style memory system for personalized AI interactions.
    
    Architecture:
    1. EXTRACT: After each conversation, extract salient facts
    2. STORE: Embed and store in user_memories table
    3. RETRIEVE: At conversation start, fetch relevant memories
    4. INJECT: Add memories to system prompt for context
    
    Memory Types:
    - semantic: Facts about user ("researches ML for robotics")
    - episodic: Past interactions ("last time you asked about...")
    - preference: User preferences ("prefers detailed explanations")
    - project: Project-specific notes ("Project X focuses on NLP")
    """
    
    def __init__(self, db, embed_model=None, llm_client=None):
        """
        Args:
            db: Database session
            embed_model: Embedding model (Nomic)
            llm_client: LLM client for extraction
        """
        self.db = db
        self.embed_model = embed_model
        self.llm = llm_client
    
    # ==================== EXTRACTION ====================
    
    async def extract_memories(
        self,
        conversation_id: str,
        user_id: str,
        messages: List[Dict[str, str]]
    ) -> List[Dict]:
        """
        Extract salient facts from a conversation.
        
        Called after conversation ends or periodically.
        
        Args:
            conversation_id: UUID of the conversation
            user_id: User ID
            messages: List of message dicts with role and content
            
        Returns:
            List of extracted memory dicts
        """
        if not self.llm:
            logger.warning("No LLM client - skipping memory extraction")
            return []
        
        # Build conversation text
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages[-10:]  # Last 10 messages max
        ])
        
        # Extraction prompt
        prompt = f"""Analyze this conversation and extract important facts about the user that would be useful to remember for future conversations.

CONVERSATION:
{conversation_text}

Extract facts such as:
- Research interests or focus areas
- Preferences (writing style, detail level, etc.)
- Projects they're working on
- Constraints or limitations they mentioned
- Goals or objectives

Return as JSON array with this structure:
[
    {{
        "memory_text": "The exact fact to remember",
        "memory_type": "semantic" | "preference" | "project",
        "category": "research_focus" | "writing_style" | "project_goal" | etc,
        "importance_score": 0.0 to 1.0
    }}
]

If no important facts to extract, return empty array: []
IMPORTANT: Return ONLY valid JSON, no markdown.
"""
        
        try:
            response = await self.llm.complete(prompt, temperature=0.2)
            
            # Parse response
            cleaned = response.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('```')[1]
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            
            memories = json.loads(cleaned)
            
            if not isinstance(memories, list):
                return []
            
            # Store each memory
            stored = []
            for mem in memories[:5]:  # Max 5 memories per extraction
                try:
                    stored_mem = await self.store_memory(
                        user_id=user_id,
                        memory_text=mem.get('memory_text', ''),
                        memory_type=mem.get('memory_type', 'semantic'),
                        category=mem.get('category'),
                        importance_score=mem.get('importance_score', 0.5),
                        source_conversation_id=conversation_id,
                        source_message=messages[-1].get('content', '') if messages else None
                    )
                    if stored_mem:
                        stored.append(stored_mem)
                except Exception as e:
                    logger.error(f"Failed to store memory: {e}")
            
            return stored
            
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            return []
    
    # ==================== STORAGE ====================
    
    async def store_memory(
        self,
        user_id: str,
        memory_text: str,
        memory_type: str = 'semantic',
        category: Optional[str] = None,
        importance_score: float = 0.5,
        source_conversation_id: Optional[str] = None,
        source_message: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Store a memory with deduplication.
        
        If a similar memory exists (>0.9 cosine similarity), 
        updates it instead of creating duplicate.
        """
        if not memory_text or len(memory_text) < 5:
            return None
        
        # Generate embedding
        embedding = None
        if self.embed_model:
            try:
                embedding = self.embed_model.get_text_embedding(memory_text)
            except Exception as e:
                logger.error(f"Embedding failed: {e}")
        
        # Check for similar existing memories (deduplication)
        if embedding:
            similar = await self._find_similar_memories(user_id, embedding, threshold=0.9)
            if similar:
                # Update existing memory instead of creating new
                existing_id = similar[0]['id']
                self.db.execute(
                    text("""
                        UPDATE user_memories SET
                            memory_text = :text,
                            importance_score = GREATEST(importance_score, :importance),
                            access_count = access_count + 1,
                            updated_at = NOW()
                        WHERE id = :id
                    """),
                    {'id': existing_id, 'text': memory_text, 'importance': importance_score}
                )
                self.db.commit()
                logger.info(f"Updated existing memory {existing_id}")
                return {"id": existing_id, "action": "updated", "memory_text": memory_text}
        
        # Insert new memory
        try:
            result = self.db.execute(
                text("""
                    INSERT INTO user_memories 
                    (user_id, memory_text, embedding, memory_type, category, 
                     importance_score, source_conversation_id, source_message)
                    VALUES (:user_id, :memory_text, :embedding, :memory_type, :category,
                            :importance, :conv_id, :source_msg)
                    RETURNING id
                """),
                {
                    'user_id': user_id,
                    'memory_text': memory_text,
                    'embedding': embedding,
                    'memory_type': memory_type,
                    'category': category,
                    'importance': importance_score,
                    'conv_id': source_conversation_id,
                    'source_msg': source_message
                }
            )
            self.db.commit()
            new_id = result.fetchone()[0]
            logger.info(f"Stored new memory {new_id}: {memory_text[:50]}...")
            return {"id": new_id, "action": "created", "memory_text": memory_text}
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            self.db.rollback()
            return None
    
    async def _find_similar_memories(
        self,
        user_id: str,
        embedding: List[float],
        threshold: float = 0.9
    ) -> List[Dict]:
        """Find memories with cosine similarity above threshold."""
        try:
            result = self.db.execute(
                text("""
                    SELECT id, memory_text, 
                           1 - (embedding <=> :embedding::vector) as similarity
                    FROM user_memories
                    WHERE user_id = :user_id
                    AND embedding IS NOT NULL
                    AND 1 - (embedding <=> :embedding::vector) > :threshold
                    ORDER BY similarity DESC
                    LIMIT 5
                """),
                {'user_id': user_id, 'embedding': embedding, 'threshold': threshold}
            )
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    # ==================== RETRIEVAL ====================
    
    async def retrieve_memories(
        self,
        user_id: str,
        query: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve relevant memories for a user.
        
        Args:
            user_id: User ID
            query: Optional query to find semantically similar memories
            memory_types: Filter by types ['semantic', 'preference', 'project']
            limit: Max memories to return
            
        Returns:
            List of memory dicts sorted by relevance
        """
        # If query provided, do semantic search
        if query and self.embed_model:
            try:
                query_embedding = self.embed_model.get_text_embedding(query)
                result = self.db.execute(
                    text("""
                        SELECT id, memory_text, memory_type, category, importance_score,
                               1 - (embedding <=> :embedding::vector) as relevance
                        FROM user_memories
                        WHERE user_id = :user_id
                        AND embedding IS NOT NULL
                        ORDER BY relevance DESC, importance_score DESC
                        LIMIT :limit
                    """),
                    {'user_id': user_id, 'embedding': query_embedding, 'limit': limit}
                )
                memories = [dict(row._mapping) for row in result.fetchall()]
                
                # Update access counts
                for mem in memories:
                    self.db.execute(
                        text("UPDATE user_memories SET access_count = access_count + 1, last_accessed_at = NOW() WHERE id = :id"),
                        {'id': mem['id']}
                    )
                self.db.commit()
                
                return memories
                
            except Exception as e:
                logger.error(f"Semantic retrieval failed: {e}")
        
        # Fallback: retrieve by importance
        type_filter = ""
        if memory_types:
            type_filter = "AND memory_type = ANY(:types)"
        
        try:
            result = self.db.execute(
                text(f"""
                    SELECT id, memory_text, memory_type, category, importance_score
                    FROM user_memories
                    WHERE user_id = :user_id
                    {type_filter}
                    ORDER BY importance_score DESC, access_count DESC
                    LIMIT :limit
                """),
                {'user_id': user_id, 'types': memory_types, 'limit': limit}
            )
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            return []
    
    # ==================== INJECTION ====================
    
    def format_memories_for_prompt(self, memories: List[Dict]) -> str:
        """
        Format memories for injection into system prompt.
        
        Returns a string like:
        "ABOUT THE USER:
        - User researches ML for robotics applications
        - User prefers concise explanations
        - Working on Project X about sentiment analysis"
        """
        if not memories:
            return ""
        
        lines = ["ABOUT THE USER (from past conversations):"]
        for mem in memories:
            lines.append(f"- {mem['memory_text']}")
        
        return "\n".join(lines)
    
    async def get_context_for_conversation(
        self,
        user_id: str,
        current_message: Optional[str] = None
    ) -> str:
        """
        Get formatted memory context for a new conversation.
        
        Args:
            user_id: User ID
            current_message: Optional current message for relevance ranking
            
        Returns:
            Formatted string to inject into system prompt
        """
        memories = await self.retrieve_memories(
            user_id=user_id,
            query=current_message,
            limit=5
        )
        return self.format_memories_for_prompt(memories)
    
    # ==================== MANAGEMENT ====================
    
    async def delete_memory(self, memory_id: int, user_id: str) -> bool:
        """Delete a specific memory (user-initiated)."""
        try:
            self.db.execute(
                text("DELETE FROM user_memories WHERE id = :id AND user_id = :user_id"),
                {'id': memory_id, 'user_id': user_id}
            )
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    async def decay_old_memories(self, user_id: str, days_old: int = 30):
        """
        Reduce importance of old, unused memories.
        Run periodically to prevent memory bloat.
        """
        try:
            self.db.execute(
                text("""
                    UPDATE user_memories SET
                        importance_score = importance_score * 0.9
                    WHERE user_id = :user_id
                    AND last_accessed_at < NOW() - INTERVAL ':days days'
                    AND access_count < 3
                """),
                {'user_id': user_id, 'days': days_old}
            )
            self.db.commit()
        except Exception as e:
            logger.error(f"Memory decay failed: {e}")
    
    async def get_user_memory_stats(self, user_id: str) -> Dict:
        """Get statistics about user's memories."""
        try:
            result = self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN memory_type = 'semantic' THEN 1 END) as semantic,
                        COUNT(CASE WHEN memory_type = 'preference' THEN 1 END) as preference,
                        COUNT(CASE WHEN memory_type = 'project' THEN 1 END) as project,
                        AVG(importance_score) as avg_importance
                    FROM user_memories
                    WHERE user_id = :user_id
                """),
                {'user_id': user_id}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else {}
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
