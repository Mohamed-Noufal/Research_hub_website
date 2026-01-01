# MVP Architecture - Literature Review Platform

## Complete System Documentation

This document provides a comprehensive view of the current MVP focused on **Literature Review** for researchers.

---

## System Overview

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                         AI RESEARCH HUB - MVP                                  │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────────┐  │
│  │   SEARCH        │──▶│   RESULTS       │──▶│      WORKSPACE              │  │
│  │                 │   │                 │   │                             │  │
│  │  SearchPage.tsx │   │ SearchResults   │   │  ┌─────────────────────┐   │  │
│  │                 │   │     .tsx        │   │  │   Library Panel     │   │  │
│  │  • arXiv API    │   │                 │   │  │   Paper Viewer      │   │  │
│  │  • Semantic S.  │   │  • Paper cards  │   │  │   Literature Review │   │  │
│  │  • OpenAlex     │   │  • Save to lib  │   │  │   AI Assistant      │   │  │
│  └─────────────────┘   └─────────────────┘   │  └─────────────────────┘   │  │
│                                               │                             │  │
└───────────────────────────────────────────────┴─────────────────────────────┴──┘
```

---

## 1. Frontend Components

### Main Pages

| Component | File | Size | Purpose |
|-----------|------|------|---------|
| **SearchPage** | `SearchPage.tsx` | 22KB | Search interface, filters, sources |
| **SearchResults** | `SearchResults.tsx` | 15KB | Results display, save to library |
| **Workspace** | `Workspace.tsx` | 34KB | Main workspace with tabs/panels |

### Workspace Components

| Component | File | Size | Purpose |
|-----------|------|------|---------|
| **LibraryPanel** | `LibraryPanel.tsx` | 18KB | Saved papers, folders, organization |
| **PaperViewer** | `PaperViewer.tsx` | 23KB | PDF viewer, metadata, abstract |
| **LiteratureReview** | `LiteratureReview.tsx` | 17KB | Projects + 6 analysis tabs |
| **AIAssistant** | `AIAssistant.tsx` | 20KB | Chat interface, tool execution |
| **AIParaphraser** | `AIParaphraser.tsx` | 20KB | Text paraphrasing tool |
| **Citations** | `Citations.tsx` | 11KB | Citation generation, formats |
| **DOIFetcher** | `DOIFetcher.tsx` | 19KB | Add paper by DOI/URL |
| **NotesEditor** | `NotesEditor.tsx` | 10KB | Rich text notes |
| **AddPaperDialog** | `AddPaperDialog.tsx` | 13KB | Manual paper entry |

### Literature Review Tabs

| Tab | File | Size | Purpose |
|-----|------|------|---------|
| **SummaryView** | `SummaryView.tsx` | 26KB | Paper summaries, key info |
| **ComparisonView** | `ComparisonView.tsx` | 29KB | Side-by-side comparison table |
| **FindingsView** | `FindingsView.tsx` | 19KB | Key findings, limitations |
| **MethodologyView** | `MethodologyView.tsx` | 17KB | Methodology explorer |
| **SynthesisView** | `SynthesisView.tsx` | 12KB | Theme-based synthesis table |
| **AnalysisView** | `AnalysisView.tsx` | 5KB | Research gaps analysis |

---

## 2. Backend API Endpoints

### Paper Management

| Endpoint | Method | File | Purpose |
|----------|--------|------|---------|
| `/papers` | GET | papers.py | List papers |
| `/papers/{id}` | GET | papers.py | Get paper details |
| `/papers/search` | POST | papers.py | Search papers (multi-source) |
| `/papers/upload` | POST | papers.py | Upload PDF |
| `/papers/download` | GET | papers_download.py | Download PDF |

### User & Library

| Endpoint | Method | File | Purpose |
|----------|--------|------|---------|
| `/users/current` | GET | users.py | Get/create user |
| `/users/saved-papers` | GET/POST | users.py | Library management |
| `/users/folders` | CRUD | folders.py | Folder organization |

### Literature Review

| Endpoint | Method | File | Purpose |
|----------|--------|------|---------|
| `/projects/{id}/synthesis` | GET/PUT/PATCH | synthesis.py | Synthesis table data |
| `/projects/{id}/methodology` | GET/PATCH | methodology.py | Methodology data |
| `/projects/{id}/comparison` | GET/PUT/PATCH | comparison.py | Comparison config |
| `/projects/{id}/findings` | GET/PATCH | findings.py | Findings & gaps |

### AI Assistant

| Endpoint | Method | File | Purpose |
|----------|--------|------|---------|
| `/agent/chat` | POST | agent.py | REST chat |
| `/agent/ws/{id}` | WebSocket | agent.py | Streaming chat |
| `/agent/conversations` | POST/GET | agent.py | Conversation CRUD |

---

## 3. Database Schema

### Core Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `papers` | Paper metadata | id, title, abstract, authors, pdf_url, arxiv_id, doi |
| `local_users` | User profiles | id (UUID), local_storage_id, created_at |
| `user_saved_papers` | Library | user_id, paper_id, folder_id, tags, rating |
| `user_notes` | Notes | user_id, paper_id, content, parent_id |

### Literature Review Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `user_literature_reviews` | Projects | id, user_id, title, description, paper_ids |
| `comparison_configs` | Comparison settings | user_id, project_id, selected_paper_ids, insights |
| `comparison_attributes` | Comparison cells | user_id, project_id, paper_id, attr_name, attr_value |
| `methodology_data` | Methodology details | user_id, project_id, paper_id, description, context |
| `synthesis_configs` | Synthesis structure | user_id, project_id, columns, rows |
| `synthesis_cells` | Synthesis data | user_id, project_id, row_id, column_id, value |
| `research_gaps` | Research gaps | user_id, project_id, description, priority |
| `literature_review_findings` | Findings | review_id, finding_text, evidence |
| `literature_review_annotations` | Annotations | review_id, paper_id, annotation_type, content |

### Research Analysis Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `paper_comparisons` | Comparison data | project_id, comparison_data (JSON) |
| `research_themes` | Theme analysis | project_id, name, description, paper_ids |
| `citation_formats` | Citations | project_id, style, template |
| `spreadsheet_templates` | Custom tables | project_id, columns, rows |
| `spreadsheet_data` | Custom data | template_id, paper_id, row_data |

### RAG Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `data_paper_chunks` | Vector store | id, text, embedding (768), metadata_ |
| `paper_chunks` | Legacy chunks | paper_id, chunk_text, chunk_index |

---

## 4. User Flow: Literature Review

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          LITERATURE REVIEW FLOW                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. SEARCH                    2. SAVE                    3. PROJECT         │
│  ┌─────────────────┐         ┌─────────────────┐        ┌───────────────┐  │
│  │ Search arXiv,   │    ──▶  │ Save to Library │   ──▶  │ Create Project│  │
│  │ Semantic Scholar│         │ Organize folders│        │ Select Papers │  │
│  └─────────────────┘         └─────────────────┘        └───────────────┘  │
│                                                                             │
│  4. ANALYZE (6 Tabs)                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ Summary  │ │ Compare  │ │ Findings │ │ Method.  │ │ Synthesis│   │   │
│  │  │          │ │          │ │          │ │          │ │          │   │   │
│  │  │ All paper│ │ Side-by- │ │ Key      │ │ Method   │ │ Theme-   │   │   │
│  │  │ overviews│ │ side     │ │ findings │ │ details  │ │ based    │   │   │
│  │  │          │ │ table    │ │ & gaps   │ │ & types  │ │ table    │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. AI ASSISTANT                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ "Compare methodologies" → AI extracts & generates comparison        │   │
│  │ "Find research gaps"    → AI analyzes papers & identifies gaps      │   │
│  │ "Summarize paper X"     → AI generates summary                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. AI Assistant Integration

### Current Tools (11 implemented)

| Tool | Purpose | Endpoint/Method |
|------|---------|-----------------|
| `semantic_search` | Search papers via RAG | RAGEngine.query() |
| `get_paper_sections` | Get specific sections | RAGEngine.retrieve_only() |
| `compare_papers` | Generate comparison | LLM + RAG |
| `extract_methodology` | Extract methodology | LLM + RAG |
| `find_research_gaps` | Identify gaps | LLM + RAG |
| `get_project_by_name` | Find project | DB query |
| `get_project_papers` | List project papers | DB query |
| `link_paper_to_project` | Add paper to project | DB insert |
| `update_comparison` | Save comparison data | /comparison API |
| `update_findings` | Save findings | /findings API |
| `update_synthesis` | Save synthesis | /synthesis API |

### Tools Needed for MVP

| Tool | Purpose | Priority | Maps To |
|------|---------|----------|---------|
| `update_methodology` | Save methodology data | HIGH | /methodology API |
| `create_project` | Create new project | HIGH | /projects API |
| `add_research_gap` | Add research gap | MEDIUM | /findings API |
| `summarize_paper` | Generate summary | HIGH | LLM call |
| `generate_citation` | Create citation | MEDIUM | Template + data |

---

## 6. Data Flow: Tab Updates

### When AI Updates a Tab

```
User: "Extract methodology for all papers"

┌──────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  AI Assistant                                                             │
│  │                                                                        │
│  ├─▶ 1. Call `extract_methodology(paper_ids)`                            │
│  │       │                                                                │
│  │       └─▶ RAGEngine.retrieve_only(section_filter=["methodology"])     │
│  │           └─▶ Returns methodology chunks                              │
│  │                                                                        │
│  ├─▶ 2. LLM summarizes methodology                                       │
│  │       └─▶ Returns structured methodology                              │
│  │                                                                        │
│  └─▶ 3. Call `update_methodology(project_id, paper_id, data)`            │
│           │                                                               │
│           └─▶ PATCH /projects/{id}/methodology/{paper_id}                │
│               └─▶ Updates `methodology_data` table                       │
│                                                                           │
│  Frontend: Methodology tab refreshes → Shows AI-extracted data          │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Current State Assessment

### What's Working ✅

| Feature | Status | Notes |
|---------|--------|-------|
| Search (arXiv, Semantic Scholar) | ✅ Working | Multi-source |
| Save to Library | ✅ Working | Folders, tags |
| Paper Viewer | ✅ Working | PDF + metadata |
| Create Project | ✅ Working | UI + API |
| Add Papers to Project | ✅ Working | Selector |
| Summary Tab | ✅ UI Ready | Needs AI auto-fill |
| Comparison Tab | ✅ UI Ready | Needs AI auto-fill |
| Methodology Tab | ✅ UI Ready | Needs AI auto-fill |
| Findings Tab | ✅ UI Ready | Needs AI auto-fill |
| Synthesis Tab | ✅ UI Ready | Manual editing |
| AI Assistant | ✅ Working | WebSocket + ReAct |

### What Needs Work 🔧

| Feature | Issue | Priority |
|---------|-------|----------|
| RAG Indexing | Slow (1-2 min/paper) | HIGH |
| Background Processing | None | HIGH |
| AI → Tab Updates | Partially connected | HIGH |
| Auto-fill Buttons | Not implemented | MEDIUM |
| Citations | Basic implementation | MEDIUM |
| Export | Not implemented | LOW |

---

## 8. Production Priorities

### Phase 1: Core Infrastructure (Week 1)
- [ ] Background processing (Celery + Redis)
- [ ] Track processing status per paper
- [ ] Health check endpoints

### Phase 2: AI Integration (Week 2)
- [ ] Connect AI tools to all tab APIs
- [ ] Add "Auto-fill with AI" buttons
- [ ] Improve prompt engineering

### Phase 3: Performance (Week 3)
- [ ] Query caching (Redis)
- [ ] Connection pooling
- [ ] Database indexes

### Phase 4: Polish (Week 4)
- [ ] Error handling
- [ ] Loading states
- [ ] Export functionality

---

## 9. File Structure

```
frontend/src/components/
├── SearchPage.tsx           # Search interface
├── SearchResults.tsx        # Results display
├── Workspace.tsx            # Main workspace
└── workspace/
    ├── AIAssistant.tsx      # AI chat
    ├── LibraryPanel.tsx     # Saved papers
    ├── PaperViewer.tsx      # PDF viewer
    ├── LiteratureReview.tsx # Projects + tabs
    └── literature-review/
        ├── SummaryView.tsx
        ├── ComparisonView.tsx
        ├── FindingsView.tsx
        ├── MethodologyView.tsx
        ├── SynthesisView.tsx
        └── AnalysisView.tsx

backend/app/
├── api/v1/
│   ├── papers.py            # Paper CRUD
│   ├── users.py             # User management
│   ├── agent.py             # AI endpoints
│   ├── synthesis.py         # Synthesis tab
│   ├── methodology.py       # Methodology tab
│   ├── comparison.py        # Comparison tab
│   └── findings.py          # Findings tab
├── agents/
│   ├── base.py              # FlexibleAgent (ReAct)
│   └── orchestrator.py      # Tool orchestration
├── core/
│   ├── rag_engine.py        # RAG + Docling
│   └── llm_client.py        # Groq LLM
└── tools/
    ├── rag_tools.py         # Search, compare, extract
    └── database_tools.py    # CRUD operations
```

---

## 10. Next Steps

1. **Review this document** - Ensure complete understanding
2. **Prioritize features** - Focus on production-critical first
3. **Start implementation** - Background processing + AI connections
4. **Test user flows** - End-to-end literature review journey
