# AI Assistant System Architecture

## Complete Technical Documentation

This document provides a comprehensive analysis of the current AI Assistant architecture, including the RAG engine, agentic system, backend API, tools, and the ReAct thought loop.

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  AIAssistant.tsx                                                    │ │
│  │  - WebSocket connection to /api/v1/agent/ws/{conversation_id}       │ │
│  │  - Sends: {message, project_id, scope, selected_paper_ids}          │ │
│  │  - Receives: {type, content, tool, step} streaming events           │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  agent.py                                                           │ │
│  │  - POST /agent/chat (REST, non-streaming)                           │ │
│  │  - WebSocket /agent/ws/{conversation_id} (streaming)                │ │
│  │  - POST /agent/conversations (create new)                           │ │
│  │  - GET /agent/conversations/{id}/history                            │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  AgentService (Singleton)                                           │ │
│  │  - Manages conversation state in DB                                 │ │
│  │  - Saves user/assistant messages                                    │ │
│  │  - Delegates to OrchestratorAgent                                   │ │
│  │  - process_message() → AsyncGenerator[Dict, None]                   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR AGENT                                │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  OrchestratorAgent                                                  │ │
│  │  - Initializes LLMClient (Groq)                                     │ │
│  │  - Creates tool definitions from rag_tools, database_tools, etc.   │ │
│  │  - Wraps tools with context (project_id, scope, paper_ids)          │ │
│  │  - process_user_message_streaming() → delegates to FlexibleAgent    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         FLEXIBLE AGENT (ReAct)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  FlexibleAgent.run_streaming()                                      │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │  ReAct Loop (max 3 iterations)                               │  │ │
│  │  │                                                              │  │ │
│  │  │  1. THINK: LLM decides action (JSON: {action, action_input}) │  │ │
│  │  │  2. ACT: Execute tool or return "Final Answer"               │  │ │
│  │  │  3. OBSERVE: Add result to history, continue loop            │  │ │
│  │  │                                                              │  │ │
│  │  │  Loop Detection: Prevents calling same tool twice            │  │ │
│  │  └──────────────────────────────────────────────────────────────┘  │ │
│  │                                                                     │ │
│  │  Streaming Events Yielded:                                          │ │
│  │  - {type: "thinking", step, message}                                │ │
│  │  - {type: "tool_selected", tool, parameters, step}                  │ │
│  │  - {type: "tool_executing", tool}                                   │ │
│  │  - {type: "tool_result", tool, result}                              │ │
│  │  - {type: "synthesizing", message}                                  │ │
│  │  - {type: "message", content}  ← Final answer                       │ │
│  │  - {type: "error", message}                                         │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                              TOOLS                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │   RAG Tools      │  │  Database Tools  │  │    PDF Tools     │        │
│  │  (rag_tools.py)  │  │ (database_tools) │  │   (pdf_tools)    │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           RAG ENGINE                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  RAGEngine (rag_engine.py)                                          │ │
│  │  - LlamaIndex PGVectorStore (768-dim Nomic embeddings)              │ │
│  │  - Docling PDF parser (equations, tables, images)                   │ │
│  │  - Hybrid Retriever (Vector + BM25 fusion)                          │ │
│  │  - Metadata filtering (paper_id, section_type)                      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 1. API Layer

### File: `backend/app/api/v1/agent.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agent/chat` | POST | REST endpoint for single request/response |
| `/agent/ws/{conversation_id}` | WebSocket | Real-time streaming with ReAct steps |
| `/agent/conversations` | POST | Create new conversation |
| `/agent/conversations/{id}/history` | GET | Retrieve message history |

### WebSocket Message Format

**Client → Server:**
```json
{
  "message": "Compare the methodologies of my papers",
  "project_id": 42,
  "scope": "project",          // "project" | "library" | "selected"
  "selected_paper_ids": [1, 2, 3]  // Only if scope == "selected"
}
```

**Server → Client (Streaming Events):**
```json
// Step 1: Thinking
{"type": "thinking", "step": 1, "message": "Analyzing your request..."}

// Step 2: Tool selected
{"type": "tool_selected", "tool": "semantic_search", "parameters": {...}, "step": 1}

// Step 3: Tool executing
{"type": "tool_executing", "tool": "semantic_search"}

// Step 4: Tool result
{"type": "tool_result", "tool": "semantic_search", "result": {...}}

// Step 5: Final answer
{"type": "synthesizing", "message": "Generating final answer..."}
{"type": "message", "content": "Based on my analysis..."}
{"type": "message_end"}
```

---

## 2. Service Layer

### File: `backend/app/services/agent_service.py`

**AgentService** is a singleton that:

1. **Initializes** OrchestratorAgent with LLMClient (lazily loads RAG)
2. **Creates conversations** in `agent_conversations` table
3. **Saves messages** in `agent_messages` table
4. **Streams events** from agent to frontend

```python
class AgentService:
    _instance = None       # Singleton pattern
    _orchestrator = None   # Shared across requests
    
    async def process_message(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        project_id: int = None,
        scope: str = 'project',
        selected_paper_ids: List[int] = None
    ) -> AsyncGenerator[Dict, None]:
        # 1. Save user message to DB
        # 2. Stream agent execution events
        # 3. Save assistant message to DB
        # 4. Yield message_end
```

---

## 3. Orchestrator Agent

### File: `backend/app/agents/orchestrator.py`

**OrchestratorAgent** is the main entry point that:

1. Creates tool definitions from `rag_tools`, `database_tools`, `pdf_tools`
2. Wraps tool functions with context injection (project_id, scope, selected_paper_ids)
3. Initializes FlexibleAgent with tools
4. Delegates execution to FlexibleAgent

### Tool Creation Flow

```python
def _create_tools(self) -> List[Tool]:
    return [
        Tool(
            name="semantic_search",
            description="Search papers using semantic similarity",
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "section_filter": {"type": "array", "description": "Filter by section type"}
            },
            function=self._wrap_rag_tool(semantic_search)  # Context injected
        ),
        # ... more tools
    ]
```

### Context Injection

The orchestrator wraps tool functions to inject:
- `project_id` - Current project context
- `scope` - "project", "library", or "selected"
- `selected_paper_ids` - If scope is "selected"
- `rag_engine` - Shared RAG engine instance
- `llm_client` - Shared LLM client

---

## 4. FlexibleAgent (ReAct Loop)

### File: `backend/app/agents/base.py`

**FlexibleAgent** implements the **ReAct pattern** (Reasoning + Acting).

### ReAct Loop Pseudocode

```python
async def run_streaming(self, input_text: str):
    history = [f"User: {input_text}"]
    last_action = None
    
    for i in range(max_iterations):  # max_iterations = 3
        # 1. THINK
        yield {"type": "thinking", "step": i+1}
        
        prompt = system_prompt + history
        response = await llm.complete(prompt)
        
        # Parse JSON: {"action": "tool_name", "action_input": {...}}
        action_data = json.loads(response)
        
        # Loop detection
        if action == last_action and action != "Final Answer":
            yield {"type": "error", "message": "Loop detected"}
            return
        
        # 2. ACT
        if action == "Final Answer":
            yield {"type": "synthesizing"}
            yield {"type": "message", "content": action_input}
            return
        
        if action in self.tools:
            yield {"type": "tool_selected", "tool": action}
            yield {"type": "tool_executing", "tool": action}
            
            observation = await tool.function(**action_input)
            
            yield {"type": "tool_result", "tool": action, "result": observation}
        
        # 3. OBSERVE
        history.append(f"Tool {action} returned: {observation}")
    
    # Max iterations reached
    yield {"type": "error", "message": "Could not complete in time"}
```

### System Prompt Structure

```
You are a helpful research assistant. You have access to the following tools:

[Tool Definitions with names, descriptions, parameters]

To use a tool, respond with JSON:
{"action": "tool_name", "action_input": {"param1": "value1"}}

To provide a final answer:
{"action": "Final Answer", "action_input": "Your response here"}

Always think step-by-step before choosing an action.
```

---

## 5. Tool Definitions

### RAG Tools (`rag_tools.py`)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `semantic_search` | Search papers by semantic similarity | query, top_k, section_filter |
| `get_paper_sections` | Retrieve specific sections from papers | section_types, paper_ids |
| `compare_papers` | Generate comparison insights | paper_ids, aspect |
| `extract_methodology` | Extract structured methodology | paper_id |
| `find_research_gaps` | Identify gaps across papers | project_id |

### Database Tools (`database_tools.py`)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `get_project_by_name` | Find project by name (fuzzy match) | project_name, user_id |
| `get_project_papers` | List papers in project | project_id |
| `link_paper_to_project` | Add paper to project | project_id, paper_id |
| `update_comparison` | Save comparison config | similarities, differences |
| `update_findings` | Save paper findings | key_finding, limitations |
| `update_methodology` | Save methodology data | methodology_summary |
| `update_synthesis` | Save synthesis results | synthesis_text, key_themes |

### PDF Tools (`pdf_tools.py`)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `download_paper_pdf` | Download PDF from URL | paper_id, pdf_url |
| `extract_pdf_metadata` | Extract title, authors, etc. | pdf_path |

---

## 6. RAG Engine

### File: `backend/app/core/rag_engine.py`

**RAGEngine** provides vector search with hybrid retrieval.

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         RAGEngine                               │
│                                                                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌──────────────┐  │
│  │   Nomic Embed   │   │   PGVectorStore │   │   Docling    │  │
│  │  (768 dims)     │   │   (PostgreSQL)  │   │  PDF Parser  │  │
│  └─────────────────┘   └─────────────────┘   └──────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Hybrid Retriever                            │   │
│  │  ┌──────────────────┐   ┌──────────────────┐            │   │
│  │  │  Vector Retriever│ + │  BM25 Retriever  │            │   │
│  │  │  (semantic)      │   │  (keyword)       │            │   │
│  │  └──────────────────┘   └──────────────────┘            │   │
│  │              Fusion: QueryFusionRetriever                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Metadata Filtering:                                            │
│  - paper_id: Filter to specific papers                          │
│  - project_id: Filter to project papers                         │
│  - section_type: intro, methodology, results, conclusion        │
└────────────────────────────────────────────────────────────────┘
```

### Key Methods

```python
class RAGEngine:
    async def ingest_paper_with_docling(self, paper_id, pdf_path, metadata):
        """Parse PDF with Docling, create embeddings, store in PGVector"""
        
    async def query(self, query_text, project_id, paper_ids, section_filter, top_k):
        """Hybrid search (Vector + BM25) with metadata filtering"""
        
    async def retrieve_only(self, query_text, project_id, paper_ids, top_k):
        """Retrieval without LLM generation (cheaper, faster)"""
```

### Chunk Storage Schema

Table: `data_paper_chunks` (LlamaIndex PGVectorStore)

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Unique node ID |
| text | TEXT | Chunk content |
| metadata_ | JSONB | paper_id, section_type, title |
| embedding | VECTOR(768) | Nomic embedding |

---

## 7. LLM Client

### File: `backend/app/core/llm_client.py`

**LLMClient** wraps Groq API for LLM completions.

```python
class LLMClient:
    def __init__(self, db=None):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"  # Fast, capable
        
    async def complete(self, prompt, temperature=0.1):
        """Single completion (used by agent ReAct loop)"""
        
    async def chat(self, messages, temperature=0.7):
        """Chat completion with message history"""
```

---

## 8. Data Flow Example

### User Request: "Compare the methodologies of papers 1 and 2"

```
1. Frontend → WebSocket → agent.py
   {"message": "Compare methodologies...", "scope": "selected", "selected_paper_ids": [1,2]}

2. agent.py → AgentService.process_message()
   - Saves user message to DB
   - Calls orchestrator.process_user_message_streaming()

3. OrchestratorAgent → FlexibleAgent.run_streaming()
   
   ITERATION 1:
   - THINK: LLM decides → {"action": "compare_papers", "action_input": {"paper_ids": [1,2], "aspect": "methodology"}}
   - ACT: Execute compare_papers tool
   - OBSERVE: Get comparison results

   ITERATION 2:
   - THINK: LLM decides → {"action": "Final Answer", "action_input": "Based on my analysis..."}
   - Return final answer

4. AgentService
   - Saves assistant message to DB
   - Yields {"type": "message_end"}

5. agent.py → WebSocket → Frontend
   - All events streamed in real-time
```

---

## 9. Current Limitations & Issues

### Performance Issues
- **RAG Ingestion**: 1-2 minutes per paper (blocking)
- **No background processing**: Uploads block until complete
- **No rate limiting**: Could crash with 100+ concurrent users

### Data Issues
- **No `local_file_path`**: PDF location not tracked in papers table
- **File/DB mismatch**: Papers in DB may not have files

### Agent Issues
- **Max 3 iterations**: May not complete complex tasks
- **Loop detection**: Prevents same tool twice (may be too aggressive)
- **No memory**: Each conversation starts fresh

---

## 10. Recommended Improvements

See [rag-background-processing.md](./rag-background-processing.md) for scalability improvements.

### Quick Wins
1. Add `local_file_path` to papers table
2. Add `processing_status` column for background jobs
3. Increase max_iterations to 5 for complex tasks
4. Add conversation context/memory

### Medium-term
1. Celery + Redis for background ingestion
2. WebSocket status updates for processing
3. Rate limiting per user

### Long-term
1. Kubernetes worker scaling
2. GPU acceleration for embeddings
3. Conversation memory with summarization
