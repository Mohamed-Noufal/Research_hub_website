# AI Agent System: Phased Implementation Plan

## Overview
Transform the current single-agent system into a production-ready multi-agent architecture with memory, task persistence, and proper validation.

---

## Phase 1: Foundation & Database (Week 1)
**Goal**: Set up the infrastructure for task tracking and memory.

### 1.1 Create New Database Tables
- [x] Create `agent_task_states` table for long-task checkpointing ✅
- [x] Create `user_memories` table for Mem0-style memory ✅
- [x] Create `data_change_history` table for rollback ✅
- [x] Add indexes to `paper_sections(user_id, paper_id)` ✅

### 1.2 Create Pydantic Schemas
- [x] `MethodologyOutput` schema matching DB ✅
- [x] `FindingsOutput` schema matching DB ✅
- [x] `ComparisonOutput` schema matching DB ✅
- [x] `SynthesisOutput` schema matching DB ✅
- [x] `SummaryOutput` schema matching DB ✅

**Learning**: SQLAlchemy migrations, Pydantic model validation

---

## Phase 2: Tool Refactoring (Week 2)
**Goal**: Add validation and structured output to all tools.

### 2.1 Refactor Extract Tools
- [x] `extract_methodology` → Returns `MethodologyOutput` ✅
- [x] Create `extract_findings` → Returns `FindingsOutput` ✅
- [x] Add retry logic on validation failure ✅

### 2.2 Refactor Write Tools
- [x] `update_methodology` → Validates before write ✅
- [x] `update_findings` → Validates before write ✅
- [x] Add history logging on every write ✅

### 2.3 Create Master Tool
- [x] Implement `fill_all_tabs(project_id)` with checkpointing ✅
- [x] Add WebSocket progress streaming ✅

**Learning**: Pydantic validation, structured LLM output, retry patterns

---

## Phase 3: Multi-Agent Architecture (Week 3)
**Goal**: Split into Main Agent + Literature Review Agent with modes.

### 3.1 Create Agent Classes
- [x] Create `MainAgent` class (5 tools: list, search, route) ✅
- [x] Create `LiteratureReviewAgent` class with mode switching ✅
- [x] Define mode-to-tools mapping ✅

### 3.2 Implement Task Delegation
- [x] Main Agent → Literature Agent handoff ✅
- [x] Result aggregation back to Main Agent ✅
- [x] Context passing between agents ✅

### 3.3 WebSocket Integration
- [x] Stream agent thinking steps ✅ (in base.py)
- [x] Stream task progress for `fill_all_tabs` ✅ (in master_tools.py)

**Learning**: Multi-agent patterns, mode-based tool loading, delegation

---

## Phase 4: Memory System (Week 4)
**Goal**: Implement Mem0-style long-term memory.

### 4.1 Memory Extraction
- [x] Extract "salient facts" after each conversation ✅
- [x] Embed and store in `user_memories` ✅

### 4.2 Memory Retrieval
- [x] Query memories at conversation start ✅
- [x] Inject into System Prompt ✅

### 4.3 Memory Deduplication
- [x] Check similarity before storing ✅
- [x] Update/merge similar memories ✅

**Learning**: Mem0 pattern, memory extraction prompts, vector dedup

---

## Phase 5: Production Hardening (Week 5)
**Goal**: Add caching, rate limits, and fallbacks.

### 5.1 Embedding Cache
- [x] Add Redis cache for embeddings ✅
- [x] Cache by text hash with 24h TTL ✅

### 5.2 Rate Limiting
- [x] Add per-user rate limit (N requests/min) ✅
- [x] Add tool timeout (30s max) ✅

### 5.3 Fallbacks
- [x] LLM fallback: Groq → OpenAI ✅
- [x] Retry with exponential backoff ✅

**Learning**: Redis caching, rate limiting patterns, resilience

---

## Phase 6: Testing & Verification (Week 6)
**Goal**: Validate the system end-to-end.

### 6.1 Unit Tests
- [x] Test Pydantic schema validation ✅
- [x] Test tool execution ✅
- [x] Test mode switching ✅

### 6.2 Integration Tests
- [x] Test full `fill_all_tabs` pipeline ✅
- [x] Test Main → LitReview delegation ✅
- [x] Test memory extraction/retrieval ✅

### 6.3 Production Verification
- [ ] Test with 10+ papers in project
- [ ] Test checkpointing (stop/resume)
- [ ] Test concurrent users

**Learning**: Async testing, mocking LLM calls, load testing

---

## Summary: Files to Create/Modify

| File | Action | Phase |
|------|--------|-------|
| `migrations/add_agent_tables.py` | CREATE | 1 |
| `app/schemas/agent_outputs.py` | CREATE | 1 |
| `app/tools/rag_tools.py` | MODIFY | 2 |
| `app/tools/literature_tools.py` | MODIFY | 2 |
| `app/tools/master_tools.py` | CREATE | 2 |
| `app/agents/main_agent.py` | CREATE | 3 |
| `app/agents/literature_agent.py` | CREATE | 3 |
| `app/core/memory_manager.py` | CREATE | 4 |
| `app/core/embedding_cache.py` | CREATE | 5 |
| `tests/test_agents.py` | CREATE | 6 |

---

## Next Step
**Start with Phase 1.1**: Create the `agent_task_states` database table.
