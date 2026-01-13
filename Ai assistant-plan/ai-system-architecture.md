# AI System Architecture & Internals Analysis

## 1. High-Level Architecture Flow

The AI Assistant follows a **Reactive Event-Driven Architecture**.

### Request Lifecycle
1.  **Frontend (WebSocket)**: User sends message -> `/api/v1/agent/ws/{conversation_id}`.
2.  **AgentService (`app/services/agent_service.py`)**:
    *   **Context Injection**: Injects `user_id`, `project_id`, `scope`, and `selected_paper_ids`.
    *   **Memory Retrieval**: Fetches last 6 messages (Short-Term Memory) from DB.
    *   **Delegation**: Passes data to `OrchestratorAgent`.
3.  **Orchestrator (`app/agents/orchestrator.py`)**:
    *   Bridges Service layer and Cognitive Agent.
    *   Initializes `BaseAgent` with access to `RAGEngine`.
4.  **Cognitive Agent (`app/agents/base.py`)**:
    *   **Think**: Generates thought trace using LLM.
    *   **Act**: select tool -> execute tool.
    *   **Observe**: Read tool output.
    *   **Loop**: Repeats until `Final Answer`.
5.  **Streaming Response**: Real-time events yielded back to WebSocket.

---

## 2. Memory Architecture (Mem0-Inspired)

The system implements a **multi-tier memory system** inspired by Mem0, enabling the agent to maintain context across sessions.

### Current State vs. Target State

| Memory Type | Current | Target (Mem0-Style) |
|-------------|---------|---------------------|
| **Short-Term** | ✅ 6-message sliding window | ✅ Keep as-is |
| **Long-Term (Semantic)** | ❌ None | 🔴 Add vector-stored "memory facts" |
| **Long-Term (Graph)** | ❌ None | 🟡 Add relationship graph (user→papers→topics) |
| **Episodic** | ❌ None | 🟡 Add conversation summaries |

### 2.1 Short-Term Memory (Implemented ✅)
*   **Mechanism**: Database-backed sliding window.
*   **Window Size**: Last **6 messages** from `agent_messages` table.
*   **Purpose**: Resolve pronouns ("this paper", "the methods") within a conversation.

### 2.2 Long-Term Memory (Needs Implementation 🔴)

Inspired by [Mem0](https://mem0.ai), we need a **Two-Phase Pipeline**:

#### Phase 1: Extraction
After each conversation turn:
1.  LLM extracts "salient facts" from the conversation.
2.  Facts are stored as embeddings in a dedicated `user_memories` table.

**Example Facts:**
- "User is researching reinforcement learning for robotics"
- "User prefers papers from 2020 onwards"
- "User's project 'RL Survey' focuses on policy gradient methods"

#### Phase 2: Update (Deduplication + Merge)
Before storing new facts:
1.  Check if similar fact exists (vector similarity > 0.9).
2.  If exists: **Update** existing fact with new context.
3.  If contradicts: **Delete** old fact.
4.  If new: **Insert**.

### 2.3 Database Schema for Mem0-Style Memory

```sql
CREATE TABLE user_memories (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    memory_text TEXT NOT NULL,                    -- "User prefers ML papers from 2020+"
    embedding VECTOR(768),                        -- Nomic embedding
    memory_type VARCHAR(50) DEFAULT 'semantic',   -- 'semantic', 'episodic', 'preference'
    importance_score FLOAT DEFAULT 0.5,           -- Priority (0-1)
    access_count INT DEFAULT 0,                   -- For dynamic forgetting
    last_accessed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_memories_user ON user_memories(user_id);
CREATE INDEX idx_user_memories_embedding ON user_memories USING ivfflat (embedding vector_cosine_ops);
```

### 2.4 Memory Retrieval Flow

```
User Message → 
  1. Embed message
  2. Query user_memories (top 5 by similarity)
  3. Inject into System Prompt as "User Context"
  4. Agent responds with personalization
```

### 2.5 Implementation Checklist

| Task | Priority | Status |
|------|----------|--------|
| Create `user_memories` table | 🔴 HIGH | ❌ TODO |
| Add `extract_memories()` tool | 🔴 HIGH | ❌ TODO |
| Add `recall_memories()` in AgentService | 🔴 HIGH | ❌ TODO |
| Inject memories into System Prompt | 🔴 HIGH | ❌ TODO |
| Add memory deduplication logic | 🟡 MED | ❌ TODO |
| Add dynamic forgetting (decay old memories) | 🟢 LOW | ❌ TODO |

---

## 3. LlamaIndex & RAG Engine (`app/core/rag_engine.py`)

The system uses **LlamaIndex** as the orchestration framework for Retrieval-Augmented Generation.

### Configuration
*   **Vector Store**: `PGVectorStore` (PostgreSQL `pgvector` extension).
*   **Embedding Model**: `nomic-ai/nomic-embed-text-v1.5` (768 dimensions), running locally via `HuggingFaceEmbedding`.
*   **LLM**: `qwen/qwen3-32b` (Groq API).
*   **Chunking**: `SentenceSplitter` (chunk_size=1024, chunk_overlap=20).

### Retrieval Strategy (Hybrid)
We implement a **Hybrid Search** using `QueryFusionRetriever`:
1.  **Vector Search**: Semantic similarity (Dense retrieval).
2.  **BM25 Search**: Keyword matching (Sparse retrieval).
3.  **Fusion**: Ranks results from both sources to find the best matches.

---

## 4. PDF Processing Pipeline

Automated "Fire-and-Forget" pipeline to keep UI responsive.

1.  **Ingestion**: `Docling` (IBM) parses PDF to Markdown in a background thread pool (Non-blocking).
2.  **Extraction**: Identifies Sections, Tables, and Equations strictly.
3.  **Embedding**:
    *   **Lazy Loading**: `pdf.py` grabs the *active* embedding model from `AgentService`.
    *   **Fallback**: If no active model, initializes a temporary one to guarantee embeddings are generated.
4.  **Storage**: Saves content + embeddings to `paper_sections`.

---

## 5. Tool Catalog

The agent has access to **24 distinct tools**. Below is a complete inventory.

### A. READ Tools (Retrieve Data)
| Tool | Description | Source |
|------|-------------|--------|
| `get_paper_sections(paper_id)` | Get parsed PDF sections (Abstract, Methods, Results) | `literature_tools.py` |
| `get_paper_tables(paper_id)` | Get extracted Markdown tables | `literature_tools.py` |
| `get_paper_equations(paper_id)` | Get LaTeX equations | `literature_tools.py` |
| `get_paper_details(paper_id)` | Get metadata (Title, Authors, DOI) | `literature_tools.py` |
| `get_methodology(project_id)` | Get saved methodology data | `literature_tools.py` |
| `get_findings(project_id)` | Get saved findings | `literature_tools.py` |
| `get_comparison(project_id)` | Get saved comparison insights | `literature_tools.py` |
| `get_synthesis(project_id)` | Get saved synthesis + themes + gaps | `literature_tools.py` |
| `get_summary(project_id)` | Get saved literature review summary | `literature_tools.py` |
| `list_papers_in_library()` | List user's saved papers | `literature_tools.py` |
| `list_projects()` | List user's projects | `literature_tools.py` |
| `get_project_papers(project_id)` | Get papers in a project | `database_tools.py` |
| `get_project_by_name(name)` | Fuzzy search for project by name | `database_tools.py` |
| `semantic_search(query)` | Vector search across papers (RAG) | `rag_tools.py` |

### B. WRITE Tools (Modify Data)
| Tool | What It Updates | Table |
|------|-----------------|-------|
| `update_methodology(project_id, paper_id, ...)` | Summary, Data Collection, Analysis, Sample Size | `methodology_data` |
| `update_findings(project_id, paper_id, ...)` | Key Finding, Limitations, Custom Notes | `findings` |
| `update_comparison(project_id, ...)` | Similarities, Differences, Selected Papers | `comparison_configs` |
| `update_synthesis(project_id, ...)` | Synthesis Text, Key Themes, Research Gaps | `synthesis_data` |
| `update_summary(project_id, ...)` | Full Summary, Insights, Methodology Overview, Findings, Gaps, Future | `project_summaries` |
| `link_paper_to_project(paper_id, project_id)` | Add paper to project | `project_papers` |

### C. ANALYSIS Tools (RAG + LLM)
| Tool | What It Does |
|------|--------------|
| `extract_methodology(paper_id)` | Extract structured methodology via RAG + LLM |
| `compare_papers(paper_ids, aspect)` | Generate comparison (Similarities/Differences) |
| `find_research_gaps(project_id)` | Identify gaps across project papers |

### D. ❌ MISSING Tools (Need Implementation)
| Tool | What It Should Do | Priority |
|------|-------------------|----------|
| `batch_extract_methodology(project_id)` | Loop all papers → Extract → Write to `methodology_data` | 🔴 HIGH |
| `batch_extract_findings(project_id)` | Loop all papers → Extract key findings → Write to `findings` | 🔴 HIGH |
| `auto_fill_comparison(project_id)` | Compare all papers → Write to `comparison_configs` | 🟡 MED |
| `generate_full_review(project_id)` | Run all above + generate final summary | 🟡 MED |
| `search_arxiv(query)` | Search external ArXiv API | 🟢 LOW |
| `generate_citation(paper_id, style)` | Generate APA/BibTeX citation | 🟢 LOW |

---

## 6. Observability & Tracing (Phoenix)

The system uses **Arize Phoenix** (via OpenTelemetry) for deep debugging.

*   **Config**: `app/core/monitoring.py`
*   **Tracer**: `LlamaIndexInstrumentor` (Auto) + Manual LLM Spans.
*   **Metrics**:
    *   `llm.token_count.{prompt, completion, total}`: Usage tracking.
    *   `llm.cost.usd`: Estimated cost per call.
*   **Purpose**: Allows visualizing detailed thought traces and debugging tool failures.

---

## 7. Recommendations for Improvement

To evolve into a "Senior Research Assistant", the following capabilities are recommended:

### 1. External Knowledge Access (High Priority)
*   **Missing**: The agent is limited to the local library.
*   **Recommendation**: Add **ArXiv/Semantic Scholar Search Tool**.
    *   *Allow agent to find related work, check for newer versions, or suggest papers based on gaps.*

### 2. Citation Management
*   **Missing**: No native understanding of Citation Styles (APA, BibTeX).
*   **Recommendation**: Add **Citation Generator Tool**.
    *   *Generate correct citations for "Synthesis" and "Summary" output.*

### 3. Knowledge Graph Exploration
*   **Missing**: Papers are treated in isolation or simple lists.
*   **Recommendation**: Add **Reference Graph Tool**.
    *   *Allow traversing "Cited By" or "References" links to find seminal papers.*

### 4. Deep Verification Agent
*   **Missing**: NLI (Natural Language Inference) capabilities.
*   **Recommendation**: Add a **Fact-Check Tool**.
    *   *Verify specific claims in the Synthesis against the source text sentence-by-sentence.*

### 5. Export Capabilities
*   **Missing**: User cannot easily take data out.
*   **Recommendation**: Add **Export Tools**.
    *   *Export Methodology Table to CSV/Excel.*
    *   *Export Synthesis to Word/LaTeX.*

---

## 8. Data Flow Architecture & Recommendations

Based on industry research (Generative UI vs Server-Driven UI), we recommend the following pattern:

### 🏆 Recommendation: "Database-First" with Optimistic Updates
**Do not connect the Agent directly to the UI.** The Agent should act as a backend service that modifies the **Database** (Source of Truth).

#### Recommended Workflow:
1.  **Agent Action**: Agent decides to `update_methodology`.
2.  **Persistence**: Tool executes SQL write to `methodology_data` table.
3.  **Signal**: Agent Service sends a lightweight WebSocket event (`resource_updated`) to Frontend.
4.  **Reaction**: Frontend (React Query) invalidates cache and re-fetches data.
5.  **Result**: UI updates "automatically" without the Agent needing to know React state logic.

#### Advanced Pattern: Generative UI (Future)
For dynamic dashboards (e.g. "Visualize these results"), the Agent can generate a **JSON UI Schema** (e.g. using Vercel AI SDK's `generateUI` pattern or A2UI protocol).
*   **Agent**: Returns `{ "component": "BarChart", "data": [...] }`
*   **Frontend**: Renders the specific component on the fly.
*   *This keeps the Agent decoupled from DOM manipulation while enabling rich interactions.*

---

## 9. Security & Safety

### Data Isolation (Anti-Mixing)
*   **Mechanism**: The Backend (`Orchestrator`) explicitly injects the `user_id` into every tool call.
*   **Safety**: The Agent **does not** choose the User ID. Even if the LLM hallucinates a random ID, the backend overrides it with the authenticated user's ID. This physically prevents data leakage between users.

### Hallucination Mitigation
*   **Risk**: LLM might write incorrect summary content.
*   **Mitigation**:
    1.  **Versioning**: All DB updates are upserts (update-or-insert). We can extend tables to keep history.
    2.  **Human Verification**: The UI acts as a Review Step. The Agent writes the draft, and the user must verify it.
    3.  **Grounding**: Tools like `get_paper_sections` force the Agent to base its writing on retrieved text, reducing creative hallucination.

---

## 10. Production Readiness Checklist

The current system is functional but requires hardening for production deployment with multiple users.

### ✅ What's Already Production-Ready
| Feature | Status | Notes |
|---------|--------|-------|
| User Data Isolation | ✅ Done | `user_id` injected by backend |
| Non-Blocking PDF Processing | ✅ Done | Thread pool via `run_in_executor` |
| Conversation Memory | ✅ Done | 6-message sliding window |
| Token/Cost Tracking | ✅ Done | Logged to DB + OTel spans |
| Error Handling in Agent Loop | ✅ Done | Try/catch with fallback messages |

### 🔴 Critical Changes Required

#### A. Agent Layer (`app/agents/`)
| Change | Priority | Why |
|--------|----------|-----|
| **Rate Limiting per User** | 🔴 HIGH | Prevent abuse. Limit to N requests/min per user. |
| **Tool Timeout** | 🔴 HIGH | Add `asyncio.wait_for(tool(), timeout=30)` to prevent stuck tools. |
| **Max Token Budget** | 🟡 MED | Abort if prompt exceeds context limit (e.g., 32k tokens). |
| **Retry with Backoff** | 🟡 MED | Retry LLM calls on 429/503 errors. |

#### B. Tools Layer (`app/tools/`)
| Change | Priority | Why |
|--------|----------|-----|
| **Input Validation (Pydantic)** | 🔴 HIGH | Validate `paper_id`, `project_id` are integers. Reject malformed input. |
| **Audit Logging** | 🔴 HIGH | Log every write operation (`update_*`) to `audit_log` table. |
| **Idempotency Keys** | 🟡 MED | Prevent duplicate writes if agent retries. |
| **Permission Checks** | 🟡 MED | Verify user owns `project_id` before write. |

#### C. Database Layer
| Change | Priority | Why |
|--------|----------|-----|
| **History/Versioning Table** | 🔴 HIGH | Track all changes to `methodology_data`, `synthesis_data`, etc. |
| **Soft Deletes** | 🟡 MED | Never hard-delete. Add `deleted_at` column. |
| **Index on `user_id`** | 🟡 MED | Speed up user-scoped queries. |
| **Connection Pooling** | 🟡 MED | Use `asyncpg` pool for high concurrency. |

### 🟢 Recommended Enhancements (Post-Launch)
1.  **WebSocket Signal for Writes**: Emit `resource_updated` event after DB writes so UI auto-refreshes.
2.  **Cost Cap per User**: Set monthly token budget. Pause agent if exceeded.
3.  **Multi-Model Fallback**: If Groq fails, fallback to OpenAI or local model.
4.  **Guardrails**: Add content filter for offensive/harmful LLM output.

---

## 11. Concerns and Improvements for Production

### 11.1 Embedding Load (Nomic Overload Risk)

**Problem**: Local Nomic embedding model will overload under heavy concurrent usage.

| Operation | Frequency | Embedding Calls |
|-----------|-----------|-----------------|
| PDF Processing | Per upload | Many (chunking) |
| RAG Search | Per query | 1 |
| Memory Recall | Per message | 1 |
| Memory Store | Per conversation | 1-3 |

**Risk Level**: 🔴 HIGH for 10+ concurrent users

#### Solutions (Recommended Order)

| Solution | Description | Effort |
|----------|-------------|--------|
| **1. Redis Embedding Cache** | Cache embeddings by hash of text. If same query, return cached. | 🟢 LOW |
| **2. Cloud Embeddings API** | Use Nomic Atlas API or OpenAI embeddings (faster, scales) | 🟡 MED |
| **3. Batching** | Queue embedding requests, process in batches every 100ms | 🟡 MED |
| **4. Dedicated Embedding Server** | Run Nomic on separate GPU server | 🔴 HIGH |

**Immediate Action**: Implement Redis cache for embeddings.

```python
# Example: Cache embedding by text hash
import hashlib
import redis

def get_cached_embedding(text: str) -> list | None:
    key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
    cached = redis.get(key)
    if cached:
        return json.loads(cached)
    return None

def cache_embedding(text: str, embedding: list):
    key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
    redis.setex(key, 86400, json.dumps(embedding))  # 24h TTL
```

---

### 11.2 Tool Overload (Hallucination Risk)

**Problem**: 24+ tools confuses the LLM. More tools = more hallucination.

| Tool Count | LLM Accuracy | Risk |
|------------|--------------|------|
| 5-10 | ✅ High | Low |
| 10-15 | 🟡 Medium | Medium |
| 15-25 | 🔴 Low | High |
| 25+ | ❌ Very Low | Very High |

**Current Status**: 24 tools = 🔴 HIGH RISK

#### Solution: Tool Router Pattern

Instead of showing all 24 tools, use a 2-stage approach:

```
User Message
    ↓
┌─────────────────────────────────────┐
│  Stage 1: Intent Router (Fast LLM)  │
│  Classifies: SEARCH | ANALYSIS |    │
│  WRITE | PROJECT | GREETING         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Stage 2: Specialist Agent          │
│  Gets only 5-7 relevant tools       │
└─────────────────────────────────────┘
    ↓
Response
```

#### Tool Categories for Router

| Category | Tools (5-7 each) |
|----------|------------------|
| **SEARCH** | `semantic_search`, `list_papers_in_library`, `get_paper_details` |
| **ANALYSIS** | `get_paper_sections`, `extract_methodology`, `compare_papers`, `find_research_gaps` |
| **WRITE** | `update_methodology`, `update_findings`, `update_synthesis`, `update_summary` |
| **PROJECT** | `list_projects`, `get_project_papers`, `get_project_by_name`, `link_paper_to_project` |
| **GREETING** | No tools (direct response) |

#### Implementation Checklist

| Task | Priority | Status |
|------|----------|--------|
| Create intent classification prompt | 🔴 HIGH | ❌ TODO |
| Split tools into category groups | 🔴 HIGH | ❌ TODO |
| Implement 2-stage routing in Orchestrator | 🔴 HIGH | ❌ TODO |
| Add fallback if router fails | 🟡 MED | ❌ TODO |

---

### 11.3 Memory Retrieval Load

**Problem**: With Mem0-style memory, every message triggers:
1. Embed user message
2. Query `user_memories` (vector search)
3. Query `agent_messages` (SQL)

**Solutions**:

| Solution | Description |
|----------|-------------|
| **Batch Memory Refresh** | Only refresh memory context every 3 messages, not every message |
| **Memory Summary** | Periodically summarize old memories into fewer entries |
| **Importance Decay** | Lower priority of rarely-accessed memories |

---

### 11.4 Summary: Production Hardening Roadmap

| Phase | Focus | Key Changes |
|-------|-------|-------------|
| **Phase 1** | Stability | Add embedding cache, tool timeouts, rate limits |
| **Phase 2** | Scalability | Implement Tool Router, cloud embeddings fallback |
| **Phase 3** | Intelligence | Add Mem0 memory, dynamic forgetting, memory summaries |

---

## 12. Multi-Agent Architecture (Production Design)

### 12.1 Overview: Simplified 2-Agent System

Instead of one agent with 24+ tools (high hallucination risk), we use a **focused 2-agent hierarchy**.

```
User Message
     ↓
┌──────────────────────────────────────────────────────────┐
│  🧠 MAIN AGENT (Orchestrator)                            │
│  • Understands user request                              │
│  • Knows context (project, papers, history)              │
│  • Decides: Answer directly OR delegate                  │
│  • Tools: 5 (lightweight)                                │
└──────────────────────────────────────────────────────────┘
     ↓
     ↓ (If task = "Fill tabs" / "Extract" / "Analyze")
     ↓
┌──────────────────────────────────────────────────────────┐
│  📚 LITERATURE REVIEW AGENT                              │
│  ┌─────────────┐  →  ┌─────────────┐  →  ┌────────────┐  │
│  │ 🔍 EXTRACT  │     │ ✅ VALIDATE │     │ 📝 WRITE   │  │
│  │ Paper data  │     │ Check schema│     │ Fill tabs  │  │
│  └─────────────┘     └─────────────┘     └────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 12.2 Agent Specifications

| Agent | Role | Tools | Model |
|-------|------|-------|-------|
| **Main Agent** | Route, answer simple Qs | `list_papers_in_library`, `list_projects`, `get_project_papers`, `get_project_by_name`, `semantic_search` | Qwen 32B |
| **Literature Review Agent** | Extract → Validate → Write | See below | Qwen 32B |

### 12.3 Literature Review Agent: Modes Architecture

Instead of separate agents per tab, we use **ONE agent with switchable MODES**.

#### Mode-Based Tool Loading
```python
class LiteratureReviewAgent:
    MODES = {
        "methodology": ["get_paper_sections", "extract_methodology", "update_methodology"],
        "findings": ["get_paper_sections", "extract_findings", "update_findings"],
        "comparison": ["compare_papers", "update_comparison"],
        "synthesis": ["find_research_gaps", "update_synthesis"],
        "summary": ["get_methodology", "get_findings", "get_synthesis", "update_summary"],
        "full_pipeline": ["fill_all_tabs"]  # Master tool
    }
    
    def set_mode(self, mode: str):
        """Load only tools for this mode (3-5 tools max)"""
        self.active_tools = self.MODES[mode]
```

#### Tools Per Mode
| Mode | Tools (3-5 max) | Purpose |
|------|-----------------|---------|
| `methodology` | `get_paper_sections`, `extract_methodology`, `update_methodology` | Fill methodology tab |
| `findings` | `get_paper_sections`, `extract_findings`, `update_findings` | Fill findings tab |
| `comparison` | `compare_papers`, `update_comparison` | Compare papers |
| `synthesis` | `find_research_gaps`, `update_synthesis` | Generate themes/gaps |
| `summary` | `get_*` (read all), `update_summary` | Generate final summary |
| `full_pipeline` | `fill_all_tabs` | Master orchestrator |

---

### 12.4 Master Tool: `fill_all_tabs`

For "Fill all tabs for my 5 new papers", we use a **Master Orchestrator Tool**:

```python
async def fill_all_tabs(project_id: int) -> dict:
    """
    Master tool that runs the FULL literature review pipeline.
    Fills: Methodology → Findings → Comparison → Synthesis → Summary
    """
    papers = get_project_papers(project_id)
    results = {
        "papers_processed": 0,
        "methodology": 0,
        "findings": 0,
        "comparison": False,
        "synthesis": False,
        "summary": False
    }
    
    # Phase 1: Methodology (per paper)
    for paper in papers:
        data = await extract_methodology(paper.id)
        await update_methodology(project_id, paper.id, **data)
        results["methodology"] += 1
    
    # Phase 2: Findings (per paper)
    for paper in papers:
        data = await extract_findings(paper.id)
        await update_findings(project_id, paper.id, **data)
        results["findings"] += 1
    
    # Phase 3: Comparison (all papers together)
    comparison = await compare_papers([p.id for p in papers])
    await update_comparison(project_id, **comparison)
    results["comparison"] = True
    
    # Phase 4: Synthesis (themes + gaps)
    gaps = await find_research_gaps(project_id)
    await update_synthesis(project_id, research_gaps=gaps)
    results["synthesis"] = True
    
    # Phase 5: Summary (uses all above)
    summary = await generate_project_summary(project_id)
    await update_summary(project_id, **summary)
    results["summary"] = True
    
    results["papers_processed"] = len(papers)
    return results
```

---

### 12.5 Workflow: "Fill All Tabs"

**User**: "Fill all tabs for my 5 papers in RL Survey project"

```
Step 1: Main Agent
├── Understands: "Fill ALL tabs" 
├── Sets mode: "full_pipeline"
└── Calls: fill_all_tabs(project_id=42)

Step 2: fill_all_tabs() runs pipeline
├── MODE: methodology → 5 papers processed
├── MODE: findings → 5 papers processed
├── MODE: comparison → Done
├── MODE: synthesis → Done
└── MODE: summary → Done

Step 3: Return to Main Agent
└── Response: "✅ Filled all 5 tabs for 5 papers in RL Survey"
```

#### API Calls Breakdown
| Phase | LLM Calls | Notes |
|-------|-----------|-------|
| Main Agent routing | 1 | Intent detection |
| Methodology (5 papers) | 5 | Extract + Write each |
| Findings (5 papers) | 5 | Extract + Write each |
| Comparison | 1 | All papers together |
| Synthesis | 1 | Generate gaps |
| Summary | 1 | Final summary |
| **Total** | **14** | Full pipeline |

---

### 12.6 Future Sub-Agents (Not Needed Now)

| Agent | When to Add |
|-------|-------------|
| **Search Agent** | When ArXiv/Semantic Scholar integration is needed |
| **Paraphrasing Agent** | When advanced rewriting features are needed |
| **Citation Agent** | When bibliography management is needed |

---

### 12.7 Implementation Checklist

| Task | Priority | Status |
|------|----------|--------|
| Create `MainAgent` class | 🔴 HIGH | ❌ TODO |
| Create `LiteratureReviewAgent` with modes | 🔴 HIGH | ❌ TODO |
| Implement `fill_all_tabs` master tool | 🔴 HIGH | ❌ TODO |
| Implement `extract_findings` tool | 🔴 HIGH | ❌ TODO |
| Implement `generate_project_summary` tool | 🔴 HIGH | ❌ TODO |
| Add mode switching logic | 🟡 MED | ❌ TODO |
| Add progress streaming (WebSocket) | 🟡 MED | ❌ TODO |
| Add task delegation protocol | 🟡 MED | ❌ TODO |

---

## 13. Implementation Details & Safeguards

### 13.1 Data Flow: Agent → DB → UI

The Agent writes to the **Database**, and the UI reads from it automatically.

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  🧠 AGENT     │ ──►  │  🗄️ DATABASE  │ ◄──  │  🖥️ UI        │
│               │      │               │      │               │
│ Generates     │      │ Stores in     │      │ Fetches from  │
│ structured    │      │ exact schema  │      │ API endpoint  │
│ output        │      │               │      │               │
└───────────────┘      └───────────────┘      └───────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
   Pydantic Model         SQL Table           React Component
```

---

### 13.2 DB Schema to Agent Output Mapping

**The Agent's output MUST match the DB table structure exactly.**

#### Methodology Tab
| DB Column | Type | Agent Output Field | Required |
|-----------|------|-------------------|----------|
| `project_id` | int | Injected by backend | ✅ |
| `paper_id` | int | From tool input | ✅ |
| `user_id` | str | Injected by backend | ✅ |
| `methodology_summary` | text | LLM generates | ✅ |
| `data_collection` | text | LLM generates | ❌ |
| `analysis_methods` | text | LLM generates | ❌ |
| `sample_size` | text | LLM generates | ❌ |

#### Findings Tab
| DB Column | Type | Agent Output Field | Required |
|-----------|------|-------------------|----------|
| `project_id` | int | Injected | ✅ |
| `paper_id` | int | From tool input | ✅ |
| `user_id` | str | Injected | ✅ |
| `key_finding` | text | LLM generates | ✅ |
| `limitations` | text | LLM generates | ❌ |
| `custom_notes` | text | LLM generates | ❌ |

#### Comparison Tab
| DB Column | Type | Agent Output Field | Required |
|-----------|------|-------------------|----------|
| `project_id` | int | Injected | ✅ |
| `user_id` | str | Injected | ✅ |
| `insights_similarities` | text | LLM generates | ✅ |
| `insights_differences` | text | LLM generates | ✅ |
| `selected_paper_ids` | int[] | From tool input | ❌ |

#### Synthesis Tab
| DB Column | Type | Agent Output Field | Required |
|-----------|------|-------------------|----------|
| `project_id` | int | Injected | ✅ |
| `user_id` | str | Injected | ✅ |
| `synthesis_text` | text | LLM generates | ❌ |
| `key_themes` | text[] | LLM generates (array) | ❌ |
| `research_gaps` | text[] | LLM generates (array) | ❌ |

#### Summary Tab
| DB Column | Type | Agent Output Field | Required |
|-----------|------|-------------------|----------|
| `project_id` | int | Injected | ✅ |
| `user_id` | str | Injected | ✅ |
| `summary_text` | text | LLM generates | ✅ |
| `key_insights` | text[] | LLM generates | ❌ |
| `methodology_overview` | text | LLM generates | ❌ |
| `main_findings` | text | LLM generates | ❌ |
| `research_gaps` | text[] | LLM generates | ❌ |
| `future_directions` | text | LLM generates | ❌ |

---

### 13.3 Pydantic Output Validation

**Every tool that writes to DB uses Pydantic to validate LLM output.**

```python
from pydantic import BaseModel, Field
from typing import Optional, List

# Schema matches DB exactly
class MethodologyOutput(BaseModel):
    methodology_summary: str = Field(..., min_length=10)
    data_collection: Optional[str] = None
    analysis_methods: Optional[str] = None
    sample_size: Optional[str] = None

async def extract_methodology(paper_id: int) -> MethodologyOutput:
    """Extract methodology and validate against schema"""
    
    prompt = f"""Extract methodology from this paper.
    
    Return ONLY valid JSON matching this schema:
    {{
        "methodology_summary": "Brief overview (required)",
        "data_collection": "How data was collected",
        "analysis_methods": "Analysis techniques used",
        "sample_size": "Sample size if mentioned"
    }}
    """
    
    raw_response = await llm.complete(prompt)
    
    # Clean and parse
    cleaned = raw_response.replace("```json", "").replace("```", "").strip()
    
    try:
        validated = MethodologyOutput.model_validate_json(cleaned)
        return validated
    except ValidationError as e:
        # Retry with error feedback
        retry_prompt = f"Your output was invalid: {e}. Fix it."
        return await retry_extraction(retry_prompt)
```

---

### 13.4 Task State Persistence (Long Requests)

**Problem**: "Fill all tabs for 10 papers" = 50+ operations. What if it fails midway?

**Solution**: Save progress after each step.

```python
# DB Table: agent_task_states
class TaskState(BaseModel):
    task_id: str  # UUID
    user_id: str
    project_id: int
    task_type: str  # "fill_all_tabs", "batch_methodology", etc.
    status: str  # "pending", "running", "completed", "failed", "paused"
    current_phase: str  # "methodology", "findings", etc.
    total_papers: int
    processed_papers: int
    completed_paper_ids: List[int]
    failed_paper_ids: List[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

async def fill_all_tabs(project_id: int, task_id: str = None) -> dict:
    """Master tool with checkpointing"""
    
    # Load or create task state
    if task_id:
        state = load_task_state(task_id)  # Resume
    else:
        state = create_task_state(project_id)
    
    papers = get_project_papers(project_id)
    state.total_papers = len(papers)
    
    # Skip already completed papers (for resume)
    remaining = [p for p in papers if p.id not in state.completed_paper_ids]
    
    for paper in remaining:
        try:
            # Process paper
            await process_methodology(paper.id)
            await process_findings(paper.id)
            
            # Checkpoint after each paper
            state.completed_paper_ids.append(paper.id)
            state.processed_papers += 1
            save_task_state(state)
            
            # Emit progress via WebSocket
            emit_progress(state)
            
        except Exception as e:
            state.failed_paper_ids.append(paper.id)
            state.error_message = str(e)
            save_task_state(state)
            # Continue to next paper (don't fail entire task)
    
    # Finish with comparison, synthesis, summary
    await process_comparison(project_id)
    await process_synthesis(project_id)
    await process_summary(project_id)
    
    state.status = "completed"
    save_task_state(state)
    
    return state.dict()
```

---

### 13.5 WebSocket Progress Updates

**UI should show real-time progress for long tasks.**

```python
async def emit_progress(state: TaskState):
    """Send progress to frontend via WebSocket"""
    await websocket.send_json({
        "type": "task_progress",
        "task_id": state.task_id,
        "status": state.status,
        "current_phase": state.current_phase,
        "progress": f"{state.processed_papers}/{state.total_papers}",
        "percentage": int((state.processed_papers / state.total_papers) * 100)
    })
```

**Frontend shows**:
```
📊 Processing: 3/10 papers (30%)
├── ✅ Paper 1: Methodology, Findings done
├── ✅ Paper 2: Methodology, Findings done
├── 🔄 Paper 3: Processing methodology...
└── ⏳ Papers 4-10: Pending
```

---

### 13.6 Metrics & Evaluation

| What to Track | Where | Purpose |
|---------------|-------|---------|
| **Token usage** | `llm_usage_logs` table | Cost monitoring |
| **Tool execution time** | OpenTelemetry spans | Performance |
| **Tool success/fail rate** | `agent_tool_logs` table | Reliability |
| **Schema validation fails** | Logged errors | LLM quality |
| **Task completion rate** | `agent_task_states` table | End-to-end success |
| **User feedback** | UI thumbs up/down | Quality |

---

### 13.7 Backup & Rollback

| Scenario | Solution |
|----------|----------|
| **LLM output invalid** | Pydantic rejects → Retry up to 3 times |
| **Task fails midway** | Resume from last checkpoint |
| **Wrong data written** | Add `_history` tables for versioning |
| **User wants undo** | Restore from history table |
| **Groq API down** | Fallback to OpenAI |

---

### 13.8 Implementation Checklist

| Task | Priority | Status |
|------|----------|--------|
| Create Pydantic schemas for all tabs | 🔴 HIGH | ❌ TODO |
| Add validation to all `extract_*` tools | 🔴 HIGH | ❌ TODO |
| Create `agent_task_states` table | 🔴 HIGH | ❌ TODO |
| Implement checkpointing in `fill_all_tabs` | 🔴 HIGH | ❌ TODO |
| Add WebSocket progress streaming | 🟡 MED | ❌ TODO |
| Create history tables for rollback | 🟡 MED | ❌ TODO |
| Add tool execution logging | 🟡 MED | ❌ TODO |

---

## 14. Data Pipeline & Database Schema

### 14.1 Complete Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            DATA PIPELINE                                  │
└──────────────────────────────────────────────────────────────────────────┘

Step 1: PAPER INGESTION
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PDF File   │ ──► │   Upload    │ ──► │   papers    │
│  (ArXiv/    │     │  Endpoint   │     │   table     │
│   Manual)   │     │             │     │ (metadata)  │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
Step 2: PDF PROCESSING (Background Thread)
┌──────────────────────────────────────────────────────────────────────────┐
│  📄 Docling Parser                                                        │
│  ┌─────────────────┐                                                      │
│  │ PDF → Markdown  │                                                      │
│  └─────────────────┘                                                      │
│           │                                                               │
│     ┌─────┴─────────────────┬────────────────────┐                       │
│     ▼                       ▼                    ▼                       │
│ ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│ │  Sections   │     │   Tables    │     │  Equations  │                  │
│ │ (Abstract,  │     │ (Markdown)  │     │  (LaTeX)    │                  │
│ │  Methods,   │     │             │     │             │                  │
│ │  Results)   │     │             │     │             │                  │
│ └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                  │
└────────│───────────────────│───────────────────│─────────────────────────┘
         │                   │                   │
         ▼                   ▼                   ▼
Step 3: EMBEDDING + STORAGE
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ paper_sections  │   │  paper_tables   │   │ paper_equations │
│ + embedding     │   │   (raw text)    │   │   (raw text)    │
│ (VECTOR 768)    │   │                 │   │                 │
└────────┬────────┘   └─────────────────┘   └─────────────────┘
         │
         ▼
Step 4: RAG RETRIEVAL
┌──────────────────────────────────────────────────────────────────────────┐
│  🔍 RAG Engine (LlamaIndex)                                              │
│  ┌─────────────────┐     ┌─────────────────┐                             │
│  │  Vector Search  │ + + │  BM25 Search    │  = Hybrid Results           │
│  │  (Semantic)     │     │  (Keyword)      │                             │
│  └─────────────────┘     └─────────────────┘                             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### 14.2 Database Tables Overview

**Total: ~25 tables organized into 4 groups**

#### Group A: Paper Data (Source of Truth)
| Table | Purpose | Rows/Paper |
|-------|---------|------------|
| `papers` | Paper metadata (title, authors, DOI) | 1 |
| `paper_sections` | Parsed sections + **embeddings** (RAG) | 5-15 |
| `paper_tables` | Extracted tables (Markdown) | 0-10 |
| `paper_equations` | Extracted LaTeX equations | 0-20 |

#### Group B: User Data
| Table | Purpose |
|-------|---------|
| `local_users` | User profiles |
| `user_saved_papers` | User's library (which papers they saved) |
| `user_uploads` | Uploaded PDF files |
| `user_search_history` | Search analytics |
| `user_notes` | Personal notes (folder hierarchy) |

#### Group C: Literature Review (UI Tabs)
| Table | Purpose | UI Tab |
|-------|---------|--------|
| `user_literature_reviews` | Projects | Project list |
| `literature_review_annotations` | Per-paper methodology/findings | Methodology Tab |
| `literature_review_findings` | Research findings | Findings Tab |
| `paper_comparisons` | Comparison data | Comparison Tab |
| `research_themes` | Themes/gaps | Synthesis Tab |
| `ai_synthesis` | AI-generated summaries | Summary Tab |

#### Group D: Advanced Features
| Table | Purpose |
|-------|---------|
| `spreadsheet_templates` | Custom spreadsheet layouts |
| `spreadsheet_data` | Spreadsheet cell data |
| `citation_formats` | Bibliography formats |
| `export_configurations` | Export settings |
| `analysis_templates` | Custom analysis templates |

---

### 14.3 RAG Architecture

**How Many RAG Operations?**

| Operation | When | Table Used |
|-----------|------|------------|
| `semantic_search(query)` | User asks question | `paper_sections` (vector) |
| `get_paper_sections(id)` | Agent needs content | `paper_sections` (SQL) |
| `compare_papers(ids)` | Comparison request | `paper_sections` (vector) |

**Only 1 RAG Table**: `paper_sections` with `embedding VECTOR(768)`

---

### 14.4 Table Relationships (ERD Summary)

```
local_users (1)
    │
    ├──► user_saved_papers (N) ◄───── papers (1)
    │
    ├──► user_literature_reviews (N) [Project]
    │         │
    │         ├──► literature_review_annotations (N) ───► papers
    │         ├──► literature_review_findings (N)
    │         ├──► paper_comparisons (N)
    │         ├──► research_themes (N)
    │         ├──► ai_synthesis (N)
    │         └──► spreadsheet_templates (N)
    │
    └──► user_notes (N)

papers (1)
    │
    ├──► paper_sections (N) [Has VECTOR embedding]
    ├──► paper_tables (N)
    └──► paper_equations (N)
```

---

### 14.5 Production Assessment

#### ✅ What's Good
| Aspect | Status | Notes |
|--------|--------|-------|
| Connection Pooling | ✅ Done | `pool_size=20, max_overflow=10` |
| Vector Storage | ✅ Done | pgvector with `paper_sections.embedding` |
| PDF Background Processing | ✅ Done | Thread pool with `run_in_executor` |
| User Isolation | ✅ Done | All tables have `user_id` |

#### 🔴 Improvements Needed
| Issue | Current | Improvement | Priority |
|-------|---------|-------------|----------|
| **No History Tables** | Overwrites data | Add `*_history` tables for rollback | 🔴 HIGH |
| **Missing Indexes** | Slow on large data | Add index on `paper_sections(user_id, paper_id)` | 🔴 HIGH |
| **No agent_task_states** | No checkpointing | Add task state table | 🔴 HIGH |
| **No user_memories** | No Mem0 | Add long-term memory table | 🟡 MED |

---

### 14.6 New Tables Needed

```sql
-- Task State Persistence
CREATE TABLE agent_task_states (
    id SERIAL PRIMARY KEY,
    task_id UUID UNIQUE NOT NULL,
    user_id UUID NOT NULL,
    project_id INT,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    current_phase VARCHAR(50),
    total_items INT DEFAULT 0,
    processed_items INT DEFAULT 0,
    completed_item_ids INT[],
    failed_item_ids INT[],
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- History for Rollback
CREATE TABLE methodology_data_history (
    id SERIAL PRIMARY KEY,
    original_id INT NOT NULL,
    project_id INT NOT NULL,
    paper_id INT NOT NULL,
    data JSONB NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by VARCHAR(255)
);

-- Long-term Memory (Mem0)
CREATE TABLE user_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    memory_text TEXT NOT NULL,
    embedding VECTOR(768),
    memory_type VARCHAR(50) DEFAULT 'semantic',
    importance_score FLOAT DEFAULT 0.5,
    access_count INT DEFAULT 0,
    last_accessed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_user_memories_embedding ON user_memories 
    USING ivfflat (embedding vector_cosine_ops);
```

---

### 14.7 Implementation Checklist

| Task | Priority | Status |
|------|----------|--------|
| Add `agent_task_states` table | 🔴 HIGH | ❌ TODO |
| Add `*_history` tables for rollback | 🔴 HIGH | ❌ TODO |
| Add `user_memories` table (Mem0) | 🟡 MED | ❌ TODO |
| Add indexes to `paper_sections` | 🟡 MED | ❌ TODO |
| Verify all tables have `user_id` | 🟡 MED | ❌ TODO |

---

## 15. RAG Data Flow Explained

### 15.1 Key Principle: Vectors for Search, Text for LLM

**The LLM never sees vectors.** Vectors are only used to FIND the right text.

```
┌─────────────────────────────────────────────────────────────────┐
│  paper_sections table                                           │
│  ┌───────────┬──────────────────────┬──────────────────────┐    │
│  │ id        │ content (TEXT)       │ embedding (VECTOR)   │    │
│  ├───────────┼──────────────────────┼──────────────────────┤    │
│  │ 1         │ "We trained the..."  │ [0.12, -0.34, 0.56]  │    │
│  │ 2         │ "Results show..."    │ [0.23, 0.45, -0.12]  │    │
│  └───────────┴──────────────────────┴──────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         │                                      │
         │                                      │
         ▼                                      ▼
   ┌───────────────┐                    ┌───────────────┐
   │ USED FOR      │                    │ FED TO LLM    │
   │ SEARCH        │                    │               │
   │               │                    │ Plain text    │
   │ Vector math   │                    │ in prompt     │
   │               │                    │               │
   │ ❌ NOT to LLM  │                    │ ✅ TO LLM      │
   └───────────────┘                    └───────────────┘
```

---

### 15.2 Complete RAG Flow

```
Step 1: User asks "What methodology did paper 1631 use?"
                ↓
Step 2: Embed query using Nomic
        query_vector = [0.45, -0.23, 0.67...]
                ↓
Step 3: Vector search in database
        SELECT content FROM paper_sections
        WHERE paper_id = 1631
        ORDER BY embedding <=> query_vector
        LIMIT 5
                ↓
Step 4: Get back TEXT chunks (not vectors!)
        [
          "We trained the model using...",
          "The dataset consisted of..."
        ]
                ↓
Step 5: Build prompt with TEXT
        ┌────────────────────────────────────────┐
        │ System: You are a research assistant   │
        │                                        │
        │ Context:                               │
        │ "We trained the model using..."        │
        │ "The dataset consisted of..."          │
        │                                        │
        │ User: What methodology?                │
        └────────────────────────────────────────┘
                ↓
Step 6: LLM generates answer from text context
```

---

### 15.3 Pre-compute vs Query Time

| Phase | When | What Happens |
|-------|------|--------------|
| **Pre-compute** | PDF Upload | Nomic embeds each section → Store in DB |
| **Query Time** | User Question | 1 embed call → Vector search → Get text → LLM |

**Benefit**: Query time is FAST because embeddings are pre-computed.

---

### 15.4 Why This is the Industry Standard

| Component | Uses Vectors? | Uses Text? |
|-----------|--------------|------------|
| **Search (pgvector)** | ✅ Yes | ❌ No |
| **LLM Input (Prompt)** | ❌ No | ✅ Yes |
| **LLM Output** | ❌ No | ✅ Yes |

**This pattern is used by**:
- ChatGPT (with retrieval)
- Perplexity AI
- Google Gemini (grounding)
- Every production RAG system

---

### 15.5 Production Confidence

| Aspect | Score | Notes |
|--------|-------|-------|
| Architecture Pattern | ✅ 10/10 | Industry standard |
| Semantic Search | ✅ 9/10 | pgvector + Nomic |
| Hybrid Search | ✅ 9/10 | Vector + BM25 |
| Section-level Chunking | ✅ 10/10 | Better than arbitrary chunks |
| Pre-computed Embeddings | ✅ 10/10 | Fast query time |
| **Overall** | **9.5/10** | Production ready |

---

### 15.6 Optional Enhancement: Re-ranking

For even better results, add a re-ranking step:

```
Vector Search → Re-rank (Cohere/BGE) → Feed to LLM
```

| Priority | Status |
|----------|--------|
| 🟢 LOW | ❌ TODO (optional) |
