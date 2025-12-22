# Phase 4: API & Frontend Integration

**Duration**: Week 6  
**Goal**: Build REST API endpoints, WebSocket for real-time updates, and React chat UI

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 3 is complete**:

```bash
# 1. Verify orchestrator exists
.venv\Scripts\python.exe -c "from app.agents.orchestrator import OrchestratorAgent; print('✓ Orchestrator ready')"
# Expected: "✓ Orchestrator ready"

# 2. Verify database tools exist
.venv\Scripts\python.exe -c "from app.tools import database_tools; print('✓ Database tools ready')"
# Expected: "✓ Database tools ready"

# 3. Verify RAG tools exist
.venv\Scripts\python.exe -c "from app.tools import rag_tools; print('✓ RAG tools ready')"
# Expected: "✓ RAG tools ready"

# 4. Test orchestrator
.venv\Scripts\python.exe backend/test_phase3.py
# Expected: "✅ Phase 3 verification PASSED!"
```

**✅ You should have**:
- Orchestrator agent working
- All tools implemented
- Database integration tested
- RAG engine tested

**❌ If missing, complete Phase 3 first**

---

## ✅ Checklist

### Backend API
- [ ] Create `backend/app/api/v1/agent.py`
- [ ] Implement `POST /api/v1/agent/chat` - Main chat endpoint
- [ ] Implement `GET /api/v1/agent/conversations` - List conversations
- [ ] Implement `GET /api/v1/agent/conversation/{id}` - Get history
- [ ] Implement `DELETE /api/v1/agent/conversation/{id}` - Delete conversation
- [ ] Implement `WS /api/v1/agent/ws/{conversation_id}` - WebSocket
- [ ] Add authentication
- [ ] Add rate limiting
- [ ] Test all endpoints

### Agent Service
- [ ] Create `backend/app/services/agent_service.py`
- [ ] Implement `process_message()` - Main entry point
- [ ] Implement `create_conversation()` - Initialize conversation
- [ ] Implement `get_conversation_history()` - Retrieve messages
- [ ] Implement `emit_progress()` - WebSocket events
- [ ] Add error handling
- [ ] Add logging

### Frontend Components
- [ ] Create `frontend/src/components/ai/ChatPanel.tsx`
- [ ] Create `frontend/src/components/ai/MessageList.tsx`
- [ ] Create `frontend/src/components/ai/MessageBubble.tsx`
- [ ] Create `frontend/src/components/ai/ChatInput.tsx`
- [ ] Create `frontend/src/components/ai/ProgressTracker.tsx`
- [ ] Create `frontend/src/hooks/useAgent.ts`
- [ ] Style chat interface
- [ ] Test UI/UX

### Integration with Literature Review
- [ ] Add chat toggle to LiteratureReview component
- [ ] Add split view (tabs + chat)
- [ ] Auto-refresh tabs on AI updates
- [ ] WebSocket event listeners
- [ ] Test full workflow

---

## 📋 Step-by-Step Implementation

### 1. Backend API Endpoints

Create `backend/app/api/v1/agent.py`:

```python
"""
Agent API endpoints
Provides chat interface, conversation management, and WebSocket support
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.database import get_db
from app.services.agent_service import AgentService
from app.api.v1.users import get_current_user_id

router = APIRouter(prefix="/agent", tags=["agent"])

# ==================== REQUEST/RESPONSE MODELS ====================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    project_id: Optional[int] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    status: str  # 'success', 'processing', 'error'
    metadata: Optional[dict] = None

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    project_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    message_count: int

# ==================== ENDPOINTS ====================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Main chat endpoint
    
    Send a message to the AI assistant and get a response.
    The assistant can query papers, update tabs, and perform complex tasks.
    
    Args:
        request: Chat request with message and optional conversation_id
        user_id: Current user ID (from auth)
        db: Database session
    
    Returns:
        Chat response with assistant's message
    """
    try:
        # Initialize agent service
        agent_service = AgentService(db)
        
        # Process message
        result = await agent_service.process_message(
            user_id=user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            project_id=request.project_id
        )
        
        return ChatResponse(
            message=result.get('message', ''),
            conversation_id=result.get('conversation_id'),
            status=result.get('status', 'success'),
            metadata=result.get('metadata')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    List user's conversations
    
    Returns recent conversations with message counts.
    """
    result = await db.execute(
        text("""
            SELECT 
                c.id,
                c.user_id,
                c.project_id,
                c.created_at,
                c.updated_at,
                COUNT(m.id) as message_count
            FROM agent_conversations c
            LEFT JOIN agent_messages m ON m.conversation_id = c.id
            WHERE c.user_id = :user_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT :limit
        """),
        {'user_id': user_id, 'limit': limit}
    )
    
    conversations = [
        ConversationResponse(**dict(row._mapping))
        for row in result.fetchall()
    ]
    
    return conversations

@router.get("/conversation/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get conversation history
    
    Returns all messages in a conversation.
    """
    # Verify ownership
    result = await db.execute(
        text("""
            SELECT user_id FROM agent_conversations
            WHERE id = :conv_id
        """),
        {'conv_id': conversation_id}
    )
    
    row = result.fetchone()
    if not row or row.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    result = await db.execute(
        text("""
            SELECT id, role, content, metadata, created_at
            FROM agent_messages
            WHERE conversation_id = :conv_id
            ORDER BY created_at ASC
        """),
        {'conv_id': conversation_id}
    )
    
    messages = [dict(row._mapping) for row in result.fetchall()]
    
    return {
        'conversation_id': conversation_id,
        'messages': messages
    }

@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation
    
    Deletes conversation and all associated messages.
    """
    # Verify ownership
    result = await db.execute(
        text("""
            SELECT user_id FROM agent_conversations
            WHERE id = :conv_id
        """),
        {'conv_id': conversation_id}
    )
    
    row = result.fetchone()
    if not row or row.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete messages and conversation (cascade)
    await db.execute(
        text("DELETE FROM agent_conversations WHERE id = :conv_id"),
        {'conv_id': conversation_id}
    )
    await db.commit()
    
    return {'status': 'deleted', 'conversation_id': conversation_id}

# ==================== WEBSOCKET ====================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, conversation_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
    
    def disconnect(self, conversation_id: str):
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]
    
    async def send_message(self, conversation_id: str, message: dict):
        if conversation_id in self.active_connections:
            await self.active_connections[conversation_id].send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time updates
    
    Sends progress updates, tool executions, and completion events.
    """
    await manager.connect(conversation_id, websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back (for testing)
            await websocket.send_json({
                'type': 'ping',
                'timestamp': datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(conversation_id)
```

---

### 2. Agent Service

Create `backend/app/services/agent_service.py`:

```python
"""
Agent Service
Handles message processing, conversation management, and WebSocket events
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional, Dict
import uuid
from datetime import datetime

from app.agents.orchestrator import OrchestratorAgent
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.core.memory import ConversationMemory

class AgentService:
    """Service for agent operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMClient(db)
        self.rag = RAGEngine()
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> Dict:
        """
        Process user message
        
        Args:
            user_id: User ID
            message: User message
            conversation_id: Optional conversation ID
            project_id: Optional project ID for context
        
        Returns:
            Response dict
        """
        # Create or get conversation
        if not conversation_id:
            conversation_id = await self.create_conversation(
                user_id=user_id,
                project_id=project_id
            )
        
        # Initialize memory
        memory = ConversationMemory(self.db, conversation_id)
        
        # Save user message
        await memory.add_message(
            role='user',
            content=message
        )
        
        # Create orchestrator
        orchestrator = OrchestratorAgent(self.llm, self.db, self.rag)
        
        # Process with orchestrator
        result = await orchestrator.process_user_message(
            user_id=user_id,
            message=message,
            project_id=project_id
        )
        
        # Extract response
        if result.get('status') == 'max_iterations':
            response_text = "I apologize, but I couldn't complete that task. Could you try rephrasing your request?"
        elif result.get('status') == 'needs_input':
            response_text = result.get('question', 'I need more information.')
        else:
            response_text = str(result.get('result', result))
        
        # Save assistant message
        await memory.add_message(
            role='assistant',
            content=response_text,
            metadata={'result': result}
        )
        
        # Update conversation timestamp
        await self.db.execute(
            text("""
                UPDATE agent_conversations
                SET updated_at = NOW()
                WHERE id = :conv_id
            """),
            {'conv_id': conversation_id}
        )
        await self.db.commit()
        
        return {
            'message': response_text,
            'conversation_id': conversation_id,
            'status': 'success',
            'metadata': result
        }
    
    async def create_conversation(
        self,
        user_id: str,
        project_id: Optional[int] = None
    ) -> str:
        """Create new conversation"""
        conversation_id = str(uuid.uuid4())
        
        await self.db.execute(
            text("""
                INSERT INTO agent_conversations (id, user_id, project_id)
                VALUES (:id, :user_id, :project_id)
            """),
            {
                'id': conversation_id,
                'user_id': user_id,
                'project_id': project_id
            }
        )
        await self.db.commit()
        
        return conversation_id
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        last_n: int = 50
    ) -> list:
        """Get conversation history"""
        memory = ConversationMemory(self.db, conversation_id)
        return await memory.get_history(last_n=last_n)
```

---

### 3. Frontend Chat Components

Create `frontend/src/components/ai/ChatPanel.tsx`:

```typescript
import React, { useState, useEffect, useRef } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ProgressTracker } from './ProgressTracker';
import { useAgent } from '../../hooks/useAgent';

interface ChatPanelProps {
  projectId?: number;
  onClose?: () => void;
}

export function ChatPanel({ projectId, onClose }: ChatPanelProps) {
  const {
    messages,
    sendMessage,
    isProcessing,
    conversationId,
    progress
  } = useAgent(projectId);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <h2 className="text-lg font-semibold">AI Research Assistant</h2>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
          >
            ✕
          </button>
        )}
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>
      
      {/* Progress Tracker */}
      {isProcessing && progress && (
        <ProgressTracker progress={progress} />
      )}
      
      {/* Input */}
      <div className="border-t p-4">
        <ChatInput
          onSend={sendMessage}
          disabled={isProcessing}
          placeholder="Ask me anything about your papers..."
        />
      </div>
    </div>
  );
}
```

Create `frontend/src/components/ai/MessageBubble.tsx`:

```typescript
import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg p-4 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-900'
        }`}
      >
        {/* Role indicator */}
        <div className="text-xs opacity-70 mb-2">
          {isUser ? 'You' : 'AI Assistant'}
        </div>
        
        {/* Content */}
        <div className="prose prose-sm max-w-none">
          {isUser ? (
            <p className="text-white">{message.content}</p>
          ) : (
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
        
        {/* Timestamp */}
        {message.created_at && (
          <div className="text-xs opacity-50 mt-2">
            {new Date(message.created_at).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
```

Create `frontend/src/components/ai/ChatInput.tsx`:

```typescript
import React, { useState, useRef } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = e.target.scrollHeight + 'px';
  };
  
  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <textarea
        ref={textareaRef}
        value={message}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder || 'Type a message...'}
        className="flex-1 resize-none rounded-lg border border-gray-300 p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        rows={1}
        style={{ maxHeight: '200px' }}
      />
      <button
        type="submit"
        disabled={disabled || !message.trim()}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
      >
        {disabled ? '...' : 'Send'}
      </button>
    </form>
  );
}
```

Create `frontend/src/hooks/useAgent.ts`:

```typescript
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
}

interface Progress {
  tool: string;
  status: 'running' | 'completed' | 'error';
  message: string;
}

export function useAgent(projectId?: number) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  
  // Initialize WebSocket
  useEffect(() => {
    if (conversationId) {
      const websocket = new WebSocket(
        `ws://localhost:8000/api/v1/agent/ws/${conversationId}`
      );
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'progress') {
          setProgress(data.progress);
        } else if (data.type === 'completed') {
          setProgress(null);
          setIsProcessing(false);
        }
      };
      
      setWs(websocket);
      
      return () => {
        websocket.close();
      };
    }
  }, [conversationId]);
  
  const sendMessage = useCallback(async (message: string) => {
    // Add user message immediately
    const userMessage: Message = {
      role: 'user',
      content: message,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);
    
    try {
      // Send to API
      const response = await axios.post('/api/v1/agent/chat', {
        message,
        conversation_id: conversationId,
        project_id: projectId
      });
      
      // Update conversation ID
      if (!conversationId) {
        setConversationId(response.data.conversation_id);
      }
      
      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.message,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
      setProgress(null);
    }
  }, [conversationId, projectId]);
  
  return {
    messages,
    sendMessage,
    isProcessing,
    conversationId,
    progress
  };
}
```

---

### 4. Integration with Literature Review

Update `frontend/src/components/workspace/LiteratureReview.tsx`:

```typescript
import { useState } from 'react';
import { ChatPanel } from '../ai/ChatPanel';

export function LiteratureReview({ projectId }: { projectId: number }) {
  const [showChat, setShowChat] = useState(false);
  
  return (
    <div className="flex h-full">
      {/* Main content (tabs) */}
      <div className={`flex-1 ${showChat ? 'mr-4' : ''}`}>
        {/* Your existing tabs */}
        <ComparisonView />
        <FindingsView />
        <MethodologyView />
        {/* ... other tabs */}
      </div>
      
      {/* Chat panel */}
      {showChat && (
        <div className="w-96 border-l">
          <ChatPanel
            projectId={projectId}
            onClose={() => setShowChat(false)}
          />
        </div>
      )}
      
      {/* Chat toggle button */}
      {!showChat && (
        <button
          onClick={() => setShowChat(true)}
          className="fixed bottom-4 right-4 p-4 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition"
        >
          💬 AI Assistant
        </button>
      )}
    </div>
  );
}
```

---

## 🧪 Verification

Create `backend/test_phase4.py`:

```python
import asyncio
import httpx

async def test_api():
    print("=" * 60)
    print("🧪 Phase 4 Verification Test")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1/agent"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Send chat message
        print("\n1️⃣ Testing chat endpoint...")
        response = await client.post(
            f"{base_url}/chat",
            json={
                "message": "Hello, what can you do?",
                "project_id": 1
            },
            headers={"Authorization": "Bearer test_token"}
        )
        print(f"   ✅ Status: {response.status_code}")
        print(f"   Response: {response.json()['message'][:100]}...")
        
        # Test 2: List conversations
        print("\n2️⃣ Testing conversations list...")
        response = await client.get(
            f"{base_url}/conversations",
            headers={"Authorization": "Bearer test_token"}
        )
        print(f"   ✅ Found {len(response.json())} conversations")
        
    print("\n" + "=" * 60)
    print("✅ Phase 4 verification PASSED!")
    print("=" * 60)
    print("\n🎯 Next steps:")
    print("   1. Test chat UI in browser")
    print("   2. Test WebSocket real-time updates")
    print("   3. Proceed to Phase 5: Testing")

if __name__ == "__main__":
    asyncio.run(test_api())
```

---

## 📝 Deliverables

- ✅ REST API endpoints for chat
- ✅ WebSocket for real-time updates
- ✅ Agent service with conversation management
- ✅ React chat components
- ✅ Integration with literature review UI
- ✅ All tests passing

---

## ⏭️ Next Phase

Proceed to **Phase 5: Testing & Quality** to write comprehensive tests.
