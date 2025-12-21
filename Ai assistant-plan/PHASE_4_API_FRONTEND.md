# Phase 4: API & Frontend Integration

**Duration**: Week 6  
**Goal**: Create API endpoints, WebSocket support, and frontend components

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 3 is complete**:

```bash
# 1. Verify orchestrator exists
python -c "from backend.app.agents.orchestrator import OrchestratorAgent; print('✓ Orchestrator ready')"
# Expected: "✓ Orchestrator ready"

# 2. Verify tools exist
python -c "from backend.app.tools.database_tools import create_database_tools; print('✓ Database tools ready')"
# Expected: "✓ Database tools ready"

# 3. Verify RAG tools exist
python -c "from backend.app.tools.rag_tools import create_rag_tools; print('✓ RAG tools ready')"
# Expected: "✓ RAG tools ready"

# 4. Test full agent workflow
python backend/test_phase3.py
# Expected: All tests pass
```

**✅ You should have**:
- Orchestrator agent working
- All tools implemented
- Agent can process messages
- Phase 3 tests passing

**❌ If missing, complete Phase 3 first**

---

## ✅ Checklist

### Backend API
- [ ] Create `backend/app/api/v1/agent.py`
- [ ] Implement `/api/v1/agent/chat` endpoint
- [ ] Implement WebSocket endpoint
- [ ] Add authentication
- [ ] Add rate limiting

### Frontend Components
- [ ] Create `frontend/src/components/ai/ChatPanel.tsx`
- [ ] Create `frontend/src/hooks/useAgent.ts`
- [ ] Add WebSocket client
- [ ] Integrate with Literature Review

---

## 📋 Implementation

### 1. Backend API

Create `backend/app/api/v1/agent.py`:

```python
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.users import get_current_user_id
from app.agents.orchestrator import OrchestratorAgent
from app.core.llm_client import LLMClient
from app.core.vector_store import VectorStore

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    project_id: Optional[int] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    status: str
    conversation_id: str
    metadata: dict = {}

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Main chat endpoint for AI assistant
    """
    # Initialize components
    llm = LLMClient(db)
    vector_store = VectorStore(db)
    orchestrator = OrchestratorAgent(llm, db, vector_store)
    
    # Process message
    result = await orchestrator.process_user_message(
        user_id=user_id,
        message=request.message,
        project_id=request.project_id
    )
    
    return ChatResponse(
        message=result.get('message', 'Task completed'),
        status=result.get('status', 'success'),
        conversation_id=request.conversation_id or "new",
        metadata=result
    )

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket for real-time progress updates
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Process with agent
            llm = LLMClient(db)
            vector_store = VectorStore(db)
            orchestrator = OrchestratorAgent(llm, db, vector_store)
            
            # Send progress updates
            async for event in orchestrator.process_with_progress(data['message']):
                await websocket.send_json(event)
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {conversation_id}")
```

### 2. Frontend Hook

Create `frontend/src/hooks/useAgent.ts`:

```typescript
import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function useAgent(projectId?: number) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      const response = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          project_id: projectId
        })
      });
      
      return response.json();
    },
    onMutate: (message) => {
      // Add user message immediately
      setMessages(prev => [...prev, {
        role: 'user',
        content: message,
        timestamp: new Date()
      }]);
      setIsProcessing(true);
    },
    onSuccess: (data) => {
      // Add assistant response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.message,
        timestamp: new Date()
      }]);
      setIsProcessing(false);
    }
  });
  
  return {
    messages,
    sendMessage: sendMessage.mutate,
    isProcessing
  };
}
```

### 3. Chat Component

Create `frontend/src/components/ai/ChatPanel.tsx`:

```typescript
import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { useAgent } from '../../hooks/useAgent';

interface ChatPanelProps {
  projectId?: number;
}

export function ChatPanel({ projectId }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const { messages, sendMessage, isProcessing } = useAgent(projectId);
  
  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };
  
  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">AI Assistant</h3>
        <p className="text-sm text-gray-500">Ask me anything about your literature review</p>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        
        {isProcessing && (
          <div className="flex items-center gap-2 text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">AI is thinking...</span>
          </div>
        )}
      </div>
      
      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your papers..."
            className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={isProcessing}
          />
          <Button
            onClick={handleSend}
            disabled={isProcessing || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-700"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
```

### 4. Integrate with Literature Review

Update `frontend/src/components/workspace/LiteratureReview.tsx`:

```typescript
import { ChatPanel } from '../ai/ChatPanel';

function LiteratureReview({ project }: { project: Project }) {
  const [showChat, setShowChat] = useState(false);
  
  return (
    <div className="flex h-full gap-4">
      {/* Existing tabs */}
      <div className={showChat ? 'w-2/3' : 'w-full'}>
        <ComparisonView papers={papers} projectId={project.id} />
        {/* Other tabs */}
      </div>
      
      {/* AI Chat Panel */}
      {showChat && (
        <div className="w-1/3">
          <ChatPanel projectId={project.id} />
        </div>
      )}
      
      {/* Toggle button */}
      <button
        onClick={() => setShowChat(!showChat)}
        className="fixed bottom-4 right-4 p-4 bg-indigo-600 text-white rounded-full shadow-lg"
      >
        <MessageSquare className="w-6 h-6" />
      </button>
    </div>
  );
}
```

---

## 🧪 Testing

```bash
# Test API endpoint
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find my AI Healthcare project"}'

# Test WebSocket
wscat -c ws://localhost:8000/api/v1/agent/ws/test-conversation
```

---

## 📝 Deliverables

- ✅ Chat API endpoint
- ✅ WebSocket support
- ✅ Frontend chat component
- ✅ Integration with Literature Review

---

## ⏭️ Next Phase

Proceed to **Phase 5: Testing & Quality Assurance**.
