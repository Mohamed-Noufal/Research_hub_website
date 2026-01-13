# Final App Analysis: Current State vs Implementation Plan

## Overview
This document provides a complete analysis of what EXISTS vs what NEEDS TO BE BUILT for the production multi-agent system.

---

## 1. Database Schema Analysis

### ✅ Already Exists (UI Tabs)

| Table | Migration | Purpose | Status |
|-------|-----------|---------|--------|
| `papers` | Base | Paper metadata | ✅ Exists |
| `paper_sections` | 025 | Parsed sections + embeddings (768 dim) | ✅ Exists |
| `paper_tables` | 025 | Extracted tables | ✅ Exists |
| `paper_equations` | 025 | LaTeX equations | ✅ Exists |
| `paper_figures` | 025 | Figures | ✅ Exists |
| `methodology_data` | 013 | Methodology tab | ✅ Exists |
| `findings` | 014 | Findings tab | ✅ Exists |
| `research_gaps` | 014 | Gaps | ✅ Exists |
| `comparison_configs` | 015 | Comparison tab | ✅ Exists |
| `comparison_attributes` | 015 | Custom comparison rows | ✅ Exists |
| `synthesis_configs` | 016 | Synthesis table structure | ✅ Exists |
| `synthesis_cells` | 016 | Synthesis cell values | ✅ Exists |
| `project_summaries` | 025 | Summary tab | ✅ Exists |
| `agent_conversations` | 020 | Chat sessions | ✅ Exists |
| `agent_messages` | 020 | Chat messages | ✅ Exists |
| `agent_tool_calls` | 020 | Tool logs | ✅ Exists |
| `llm_usage_logs` | 020 | Token/cost tracking | ✅ Exists |
| `rag_usage_logs` | 020 | RAG performance | ✅ Exists |
| `paper_chunks` | 020 | Older chunking (384 dim) | ✅ Exists (legacy) |

### 🔴 Needs to be Created

| Table | Purpose | Priority |
|-------|---------|----------|
| `agent_task_states` | Long-task checkpointing | 🔴 HIGH |
| `user_memories` | Mem0-style memory | 🟡 MED |
| `methodology_data_history` | Rollback support | 🟡 MED |
| `findings_history` | Rollback support | 🟡 MED |

---

## 2. Agent System Analysis

### ✅ Already Exists

| Component | File | Description | Status |
|-----------|------|-------------|--------|
| `FlexibleAgent` | `base.py` | ReAct loop with streaming | ✅ Working |
| `OrchestratorAgent` | `orchestrator.py` | Main agent, creates all tools | ✅ Working |
| Tool registration | `orchestrator.py` | 24 tools registered | ✅ Working |
| Context injection | `orchestrator.py` | user_id injected | ✅ Working |
| Chat history | `agent_service.py` | 6-message window | ✅ Working |

### 🔴 Needs to be Created

| Component | Purpose | Priority |
|-----------|---------|----------|
| `MainAgent` | Router, lightweight (5 tools) | 🔴 HIGH |
| `LiteratureReviewAgent` | Mode-based, 12 tools | 🔴 HIGH |
| Mode switching logic | Load tools per mode | 🔴 HIGH |
| Task delegation | Main → SubAgent handoff | 🔴 HIGH |
| `fill_all_tabs` tool | Master pipeline | 🔴 HIGH |

---

## 3. Tools Analysis

### ✅ Already Exists

#### Read Tools (14 total)
| Tool | File | Status |
|------|------|--------|
| `get_paper_sections` | literature_tools.py | ✅ |
| `get_paper_tables` | literature_tools.py | ✅ |
| `get_paper_equations` | literature_tools.py | ✅ |
| `get_paper_details` | literature_tools.py | ✅ |
| `get_methodology` | literature_tools.py | ✅ |
| `get_findings` | literature_tools.py | ✅ |
| `get_comparison` | literature_tools.py | ✅ |
| `get_synthesis` | literature_tools.py | ✅ |
| `get_summary` | literature_tools.py | ✅ |
| `list_papers_in_library` | literature_tools.py | ✅ |
| `list_projects` | literature_tools.py | ✅ |
| `get_project_by_name` | database_tools.py | ✅ |
| `get_project_papers` | database_tools.py | ✅ |
| `semantic_search` | rag_tools.py | ✅ |

#### Write Tools (6 total)
| Tool | File | Status |
|------|------|--------|
| `update_methodology` | database_tools.py | ✅ |
| `update_findings` | database_tools.py | ✅ |
| `update_comparison` | database_tools.py | ✅ |
| `update_synthesis` | database_tools.py | ✅ |
| `update_summary` | literature_tools.py | ✅ |
| `link_paper_to_project` | database_tools.py | ✅ |

#### Analysis Tools (4 total)
| Tool | File | Status |
|------|------|--------|
| `extract_methodology` | rag_tools.py | ✅ |
| `compare_papers` | rag_tools.py | ✅ |
| `find_research_gaps` | rag_tools.py | ✅ |
| `get_paper_sections` (RAG) | rag_tools.py | ✅ |

### 🔴 Needs to be Created

| Tool | Purpose | Priority |
|------|---------|----------|
| `extract_findings` | LLM extraction | 🔴 HIGH |
| `fill_all_tabs` | Master pipeline | 🔴 HIGH |
| `batch_extract_methodology` | Loop all papers | 🟡 MED |
| `batch_extract_findings` | Loop all papers | 🟡 MED |
| `generate_project_summary` | Aggregate summary | 🟡 MED |

---

## 4. Schema Validation Analysis

### 🔴 NOT YET IMPLEMENTED

Currently, tools return free-form dicts. We need Pydantic schemas:

| Schema | Matches Table | Status |
|--------|---------------|--------|
| `MethodologyOutput` | methodology_data | 🔴 TODO |
| `FindingsOutput` | findings | 🔴 TODO |
| `ComparisonOutput` | comparison_configs | 🔴 TODO |
| `SynthesisOutput` | synthesis_configs | 🔴 TODO |
| `SummaryOutput` | project_summaries | 🔴 TODO |

---

## 5. RAG System Analysis

### ✅ Already Exists

| Component | Status | Notes |
|-----------|--------|-------|
| Nomic embeddings (768 dim) | ✅ | Via HuggingFace |
| pgvector storage | ✅ | paper_sections.embedding |
| Hybrid search | ✅ | Vector + BM25 |
| LlamaIndex integration | ✅ | RAGEngine class |
| Section-level chunking | ✅ | Better than arbitrary |

### 🔴 Needs Improvement

| Issue | Improvement | Priority |
|-------|-------------|----------|
| No embedding cache | Add Redis cache | 🔴 HIGH |
| Local Nomic load | Cloud fallback option | 🟡 MED |
| No re-ranking | Add Cohere rerank | 🟢 LOW |

---

## 6. Production Features Analysis

### ✅ Already Exists

| Feature | Location | Status |
|---------|----------|--------|
| Connection pooling | database.py | ✅ (pool_size=20) |
| LLM token logging | llm_usage_logs | ✅ |
| Tool call logging | agent_tool_calls | ✅ |
| RAG usage logging | rag_usage_logs | ✅ |
| OpenTelemetry tracing | monitoring.py | ✅ |
| User isolation | Context injection | ✅ |

### 🔴 Needs Implementation

| Feature | Purpose | Priority |
|---------|---------|----------|
| Rate limiting | Prevent abuse | 🔴 HIGH |
| Tool timeout | 30s max | 🔴 HIGH |
| Task checkpointing | Resume failed tasks | 🔴 HIGH |
| WebSocket progress | Real-time UI updates | 🟡 MED |
| LLM fallback | Groq → OpenAI | 🟡 MED |
| History tables | Rollback | 🟡 MED |

---

## 7. Updated Implementation Plan

Based on this analysis, here's the **revised phase breakdown**:

### Phase 1: Database (3 days)
- [ ] Create migration: `agent_task_states`
- [ ] Create migration: `user_memories`
- [ ] Create Pydantic schemas for all 5 tabs
- [ ] File: `app/schemas/agent_outputs.py`

### Phase 2: Tools (4 days)
- [ ] Add `extract_findings` tool
- [ ] Add Pydantic validation to `extract_methodology`
- [ ] Create `fill_all_tabs` master tool
- [ ] Add retry logic on validation failure
- [ ] File: `app/tools/master_tools.py`

### Phase 3: Multi-Agent (5 days)
- [ ] Create `MainAgent` class (5 tools)
- [ ] Create `LiteratureReviewAgent` with modes
- [ ] Implement mode switching
- [ ] Implement task delegation
- [ ] Update `orchestrator.py` to use new agents

### Phase 4: Memory (3 days)
- [ ] Implement memory extraction after conversations
- [ ] Implement memory retrieval before agent runs
- [ ] Add deduplication logic
- [ ] File: `app/core/memory_manager.py`

### Phase 5: Production (3 days)
- [ ] Add Redis embedding cache
- [ ] Add rate limiting middleware
- [ ] Add tool timeout wrapper
- [ ] Add LLM fallback

### Phase 6: Testing (2 days)
- [ ] Unit tests for schemas
- [ ] Integration tests for `fill_all_tabs`
- [ ] Load testing with 10+ papers

---

## 8. Quick Reference: What to Build

### New Files to Create
| File | Contents |
|------|----------|
| `migrations/026_agent_enhancements.sql` | task_states, memories tables |
| `app/schemas/agent_outputs.py` | Pydantic models |
| `app/tools/master_tools.py` | fill_all_tabs |
| `app/agents/main_agent.py` | Router agent |
| `app/agents/literature_agent.py` | Mode-based agent |
| `app/core/memory_manager.py` | Mem0 implementation |
| `app/core/embedding_cache.py` | Redis cache |
| `tests/test_multi_agent.py` | Test suite |

### Files to Modify
| File | Changes |
|------|---------|
| `app/tools/rag_tools.py` | Add validation, extract_findings |
| `app/agents/orchestrator.py` | Use new agent classes |
| `app/services/agent_service.py` | Add memory retrieval |

---

## Summary

| Category | Exists | To Build |
|----------|--------|----------|
| **Database Tables** | 18 | 4 |
| **Tools** | 24 | 5 |
| **Agents** | 2 | 2 |
| **Schemas** | 0 | 5 |
| **Production Features** | 6 | 6 |

**Total effort estimate**: ~20 days (4 weeks at 5 days/week)
