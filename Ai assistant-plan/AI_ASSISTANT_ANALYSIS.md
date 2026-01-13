# 🔬 Research Paper Search Platform - Complete Analysis

> **Date**: 2026-01-04 (Updated)  
> **Purpose**: Comprehensive analysis of the entire project architecture for AI Assistant and RAG pipeline.

---

## 📦 Project Overview

A full-stack academic research paper search and literature review platform with:
- **Multi-source paper search** (arXiv, Semantic Scholar, OpenAlex, PubMed, Europe PMC, CORE)
- **AI-powered analysis** (embeddings, query analysis, RAG)
- **Literature review workflow** (methodology, findings, comparison, synthesis)
- **AI Assistant** with ReAct agent pattern
- **Automatic PDF processing** for structured content extraction

---

## 🏗️ Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                 │
│   SearchPage → SearchResults → Workspace → LiteratureReview │
│                           ↓                                 │
│                    AIAssistant (WebSocket)                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ↓ HTTP / WebSocket ↓
┌────────────────────────────┴────────────────────────────────┐
│                     BACKEND (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 16 API Routers:                                         ││
│  │  papers, users, agent, pdf, search-history, folders,    ││
│  │  table-config, methodology, findings, comparison,       ││
│  │  synthesis, analysis, knowledge-base, async-upload,     ││
│  │  health, metrics                                        ││
│  └─────────────────────────────────────────────────────────┘│
│                             ↓                               │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐│
│  │ AgentService │  │ RAGEngine   │  │ UnifiedSearchService ││
│  │  ↓           │  │  ↓          │  │  ↓                   ││
│  │ Orchestrator │  │ LlamaIndex  │  │ Multi-source         ││
│  │  ↓           │  │ Nomic 768d  │  │ (arXiv, S2, OA...)   ││
│  │ FlexibleAgent│  │ Docling PDF │  │                      ││
│  │  ↓           │  │      ↓      │  │                      ││
│  │ 21 Tools     │  │ PDFExtractor│  │                      ││
│  └─────────────┘  └─────────────┘  └───────────────────────┘│
└────────────────────────────┬────────────────────────────────┘
                             │
                    ↓ PostgreSQL + Redis ↓
┌─────────────────────────────────────────────────────────────┐
│                       DATABASE                               │
│  papers, local_users, user_saved_papers, user_notes,        │
│  user_literature_reviews, comparison_configs, findings,     │
│  synthesis_configs, methodology_data, paper_chunks,         │
│  agent_conversations, agent_messages, llm_usage_logs,       │
│  paper_sections, paper_figures, paper_tables,               │
│  paper_equations, project_summaries                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Complete API Endpoint Map

### Papers & Search
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/papers/search` | GET | Unified multi-source search |
| `/api/v1/papers/ai-suggestions` | GET | AI query recommendations |
| `/api/v1/papers/manual` | POST | Create manual paper |
| `/api/v1/papers/health` | GET | Service health check |
| `/api/v1/papers/stats` | GET | Database statistics |
| `/api/v1/papers/categories` | GET | Available search categories |
| `/api/v1/papers/generate-embeddings` | POST | Generate paper embeddings |

### PDF Processing (NEW)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/pdf/process` | POST | Process PDF → extract content |
| `/api/v1/pdf/status/{id}` | GET | Get processing status |
| `/api/v1/pdf/batch-process` | POST | Queue multiple PDFs |

### Users & Library
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/users/init` | POST | Initialize user session |
| `/api/v1/users/saved-papers` | GET/POST | Library management |
| `/api/v1/users/saved-papers/{id}` | DELETE | Remove from library |
| `/api/v1/users/notes` | GET/POST | Notes CRUD |
| `/api/v1/users/notes/hierarchy` | GET | Folder structure |
| `/api/v1/users/literature-reviews` | GET/POST/PUT/DELETE | Project CRUD |
| `/api/v1/users/literature-reviews/{id}/seed` | POST | Seed project data |

### Literature Review Workflow
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/projects/{id}/methodology` | GET/PATCH | Methodology data |
| `/api/v1/projects/{id}/findings` | GET | All paper findings |
| `/api/v1/projects/{id}/findings/{paper_id}` | PATCH | Update finding |
| `/api/v1/projects/{id}/findings/gaps` | GET/POST | Research gaps |
| `/api/v1/projects/{id}/comparison/config` | GET/PUT | Comparison settings |
| `/api/v1/projects/{id}/comparison/attributes` | GET/PATCH | Attribute values |
| `/api/v1/projects/{id}/synthesis` | GET | Synthesis table |
| `/api/v1/projects/{id}/synthesis/structure` | PUT | Update structure |
| `/api/v1/projects/{id}/synthesis/cells` | PATCH | Update cell |

### AI Agent
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/agent/chat` | POST | REST chat (collects all) |
| `/api/v1/agent/conversations` | POST | Create conversation |
| `/api/v1/agent/conversations/{id}/history` | GET | Message history |
| `/api/v1/agent/ws/{id}?user_id=X` | WebSocket | Real-time streaming |

---

## 🗄️ Database Schema

> **Database**: PostgreSQL with pgvector  
> **Tables**: 46 total (41 original + 5 new content tables)

### NEW Tables (Paper Content Extraction)
| Table | Purpose |
|-------|---------|
| `paper_sections` | Text sections (abstract, methodology, etc.) + 768-dim embeddings |
| `paper_figures` | Image metadata + captions + file paths |
| `paper_tables` | Table data as markdown/JSON |
| `paper_equations` | LaTeX equations + context |
| `project_summaries` | AI-generated project summaries |

### Core Tables
| Table | Purpose |
|-------|---------|
| `papers` | Global paper repository (386+ rows) |
| `local_users` | User accounts (UUID) |
| `user_saved_papers` | User library with tags/notes |
| `user_notes` | Hierarchical notes with folders |
| `user_literature_reviews` | Projects with status/metadata |

### Literature Review Tables
| Table | Purpose |
|-------|---------|
| `project_papers` | Paper-to-project mapping |
| `methodology_data` | Per-paper methodology analysis |
| `findings` | Key findings + limitations |
| `comparison_configs` | Selected papers + insights |
| `comparison_attributes` | Cell-level attribute data |
| `synthesis_configs` | Table structure (columns/rows) |
| `synthesis_cells` | Cell values |
| `research_gaps` | Identified gaps |

### AI/RAG Tables
| Table | Purpose |
|-------|---------|
| `data_paper_chunks` | RAG chunks with 768-dim embeddings (256 rows) |
| `agent_conversations` | Chat sessions |
| `agent_messages` | User/assistant messages |
| `agent_tool_calls` | Tool execution logs |
| `llm_usage_logs` | Token/cost tracking |

---

## � RAG Engine & PDF Parsing Workflow

### RAG Engine Overview (`rag_engine.py`)

The RAG (Retrieval-Augmented Generation) engine uses **LlamaIndex** with **Nomic embeddings** to provide semantic search across paper content.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           RAG ENGINE                                     │
│                                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────────────────┐   │
│  │ NomicEmbed  │───▶│ PGVectorStore │───▶│ VectorStoreIndex         │   │
│  │ 768 dims    │    │ paper_chunks  │    │ + BM25 Hybrid Retrieval  │   │
│  └─────────────┘    └──────────────┘    └───────────────────────────┘   │
│         ▲                                          │                     │
│         │                                          ▼                     │
│  ┌──────┴───────┐                         ┌───────────────┐             │
│  │ Docling PDF  │                         │ Query Engine  │             │
│  │ Parser       │                         │ + Redis Cache │             │
│  └──────────────┘                         └───────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

### RAG Configuration
| Component | Setting |
|-----------|---------|
| **Embedding Model** | `nomic-ai/nomic-embed-text-v1.5` |
| **Embedding Dimension** | 768 |
| **Vector Store** | PostgreSQL + pgvector |
| **Chunk Size** | 512 tokens |
| **Chunk Overlap** | 50 tokens |
| **Retrieval** | Hybrid (Vector 70% + BM25 30%) |
| **Cache** | Redis (30 min TTL) |
| **Top-K** | 10 results default |

### RAG Query Workflow

```
User Query: "What methodology did Smith use?"
                    │
                    ▼
        ┌───────────────────────┐
        │ 1. Scope Determination │
        │    - user_id          │
        │    - project_id       │
        │    - paper_ids        │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 2. Check Redis Cache  │
        │    (30 min TTL)       │
        └───────────┬───────────┘
                    │
           HIT ◄────┼────► MISS
            │               │
            │               ▼
            │     ┌─────────────────────┐
            │     │ 3. Hybrid Retrieval │
            │     │    Vector + BM25    │
            │     └─────────┬───────────┘
            │               │
            │               ▼
            │     ┌─────────────────────┐
            │     │ 4. Filter by Scope  │
            │     │    (MetadataFilters)│
            │     └─────────┬───────────┘
            │               │
            └───────┬───────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 5. Return Results     │
        │    - text chunks      │
        │    - paper metadata   │
        │    - relevance scores │
        └───────────────────────┘
```

---

## 📄 PDF Parsing & Content Extraction

### Two-Phase Processing

When a PDF is uploaded/saved, **two parallel processes** run:

```
                    PDF Upload/Save
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌──────────────────────┐      ┌──────────────────────┐
│ PHASE 1: RAG Ingest  │      │ PHASE 2: Content     │
│ (ingest_paper_with_  │      │ Extraction           │
│  docling)            │      │ (process_and_store_  │
│                      │      │  pdf)                │
│ • Docling parse      │      │                      │
│ • Export to markdown │      │ • Extract sections   │
│ • Chunk (512 tokens) │      │ • Extract tables     │
│ • Generate embeddings│      │ • Extract equations  │
│ • Store in paper_    │      │ • Store in paper_    │
│   chunks             │      │   sections/tables/   │
│                      │      │   equations          │
└──────────┬───────────┘      └──────────┬───────────┘
           │                             │
           └──────────┬──────────────────┘
                      │
                      ▼
              Paper is_processed = TRUE
```

### PDF Extractor Functions (`pdf_extractor.py`)

| Function | Purpose |
|----------|---------|
| `extract_sections_from_markdown()` | Parse headings → sections (abstract, methodology, etc.) |
| `extract_tables_from_docling()` | Extract tables from Docling result |
| `extract_equations_from_markdown()` | Extract LaTeX equations ($...$, $$...$$) |
| `process_and_store_pdf()` | Main async function that orchestrates extraction |

### Section Detection Patterns

```python
section_patterns = {
    'abstract': r'(?i)^#+\s*abstract',
    'introduction': r'(?i)^#+\s*introduction',
    'methodology': r'(?i)^#+\s*(methodology|methods|materials\s+and\s+methods)',
    'results': r'(?i)^#+\s*results',
    'discussion': r'(?i)^#+\s*discussion',
    'conclusion': r'(?i)^#+\s*(conclusion|conclusions)',
    'references': r'(?i)^#+\s*references',
    'related_work': r'(?i)^#+\s*(related\s+work|literature\s+review|background)',
}
```

### Content Storage Schema

```sql
-- paper_sections (text content)
paper_id, section_type, section_title, content, word_count, embedding, order_index

-- paper_tables (structured data)
paper_id, table_number, caption, content_markdown, content_json, row_count, column_count

-- paper_equations (math)
paper_id, equation_number, latex, mathml, context, page_number

-- paper_figures (images)
paper_id, figure_number, caption, image_path, image_url, width, height, format
```

---

## 🔄 Complete Data Flow

### End-to-End: Paper to AI Response

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PAPER INGESTION                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PDF Upload ───▶ Docling Parse ───▶ ┌─────────────────┐                    │
│        │                              │ Markdown Export │                    │
│        │                              └────────┬────────┘                    │
│        ▼                                       │                             │
│   ┌─────────────────┐                          │                             │
│   │ papers table    │◀─────────────────────────┘                             │
│   │ (metadata)      │                                                        │
│   └────────┬────────┘                                                        │
│            │                    ┌──────────────────────────────┐             │
│            │                    │     PARALLEL PROCESSING      │             │
│            │                    ├──────────────┬───────────────┤             │
│            ▼                    ▼              ▼               ▼             │
│   ┌─────────────┐      ┌──────────────┐ ┌───────────┐ ┌──────────────┐      │
│   │ paper_chunks│      │paper_sections│ │paper_     │ │paper_        │      │
│   │ (embeddings)│      │(text content)│ │tables     │ │equations     │      │
│   └─────────────┘      └──────────────┘ └───────────┘ └──────────────┘      │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. USER QUERY                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   User: "Summarize methodology from paper 123"                               │
│         │                                                                    │
│         ▼                                                                    │
│   ┌──────────────┐                                                          │
│   │ AI Agent     │                                                          │
│   │ (Orchestrator)◀──────── Tools Available ────────────────────────────┐   │
│   └──────┬───────┘                                                      │   │
│          │                                                              │   │
│          │ Thinks: "I need to get the methodology section"              │   │
│          │                                                              │   │
│          ▼                                                              │   │
│   ┌──────────────────────────────────────────────────────────────────┐ │   │
│   │ Tool: get_paper_sections(paper_id=123, section_types=['method']) │ │   │
│   └──────────────────────────────────────────────────────────────────┘ │   │
│          │                                                              │   │
│          ▼                                                              │   │
│   ┌──────────────┐                                                      │   │
│   │ paper_sections│──▶ "The study used a survey of 500 participants..." │   │
│   └──────────────┘                                                      │   │
│          │                                                              │   │
│          ▼                                                              │   │
│   AI generates summary based on ACTUAL paper content (no hallucination)     │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. OPTIONAL: SAVE TO LITERATURE REVIEW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   AI calls: update_methodology(project_id=1, paper_id=123,                   │
│             methodology_summary="Survey study...", sample_size="500")        │
│         │                                                                    │
│         ▼                                                                    │
│   ┌──────────────────┐                                                      │
│   │ methodology_data │                                                      │
│   │ table            │                                                      │
│   └──────────────────┘                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Files in Workflow

| Step | File | Function |
|------|------|----------|
| PDF Parse | `rag_engine.py` | `ingest_paper_with_docling()` |
| Content Extract | `pdf_extractor.py` | `process_and_store_pdf()` |
| Section Detection | `pdf_extractor.py` | `extract_sections_from_markdown()` |
| RAG Query | `rag_engine.py` | `query()`, `retrieve_only()` |
| Agent Tools | `literature_tools.py` | `get_paper_sections()`, etc. |
| Agent Execute | `orchestrator.py` | `process_message()` |

---

## �🤖 AI Assistant Details

### Agent Architecture
```
OrchestratorAgent
    ↓ creates
FlexibleAgent (ReAct pattern)
    ↓ uses
21 Tools:
├── Database: get_project_by_name, get_project_papers, update_comparison, 
│             update_findings, update_methodology, update_synthesis
├── RAG: semantic_search, compare_papers, extract_methodology, get_paper_sections
├── Jobs: parse_pdf, check_job_status
└── Literature (NEW):
    ├── READ: get_paper_sections, get_paper_tables, get_methodology,
    │         get_findings, get_comparison, get_synthesis, get_summary,
    │         list_papers_in_library, list_projects
    └── WRITE: update_summary
```

### LLM Configuration
| Setting | Value |
|---------|-------|
| Provider | Groq (AsyncGroq) |
| Model | `qwen/qwen3-32b` |
| Max Iterations | 3 |
| Temperature | 0.1 (agent), 0.5 (default) |
| Max Tokens | 1024 |
| Retry | 2 attempts |

### RAG Configuration
| Setting | Value |
|---------|-------|
| Embeddings | nomic-ai/nomic-embed-text-v1.5 (768 dims) |
| Chunk Size | 512 tokens |
| Chunk Overlap | 50 tokens |
| Retrieval | Hybrid (Vector + BM25) |
| PDF Parser | Docling |
| Cache | Redis (30 min TTL) |

---

## 🔄 PDF Processing Pipeline (NEW)

### Auto-Trigger Flow
```
User saves paper to library ─────────────────┐
                                             ▼
User uploads PDF ─────────────────────────┐  │
                                          ▼  ▼
                                   Check: Already processed?
                                          │
                              YES ◄───────┼───────► NO
                              (skip)              │
                                                  ▼
                              Parse PDF with Docling
                                          │
                              ┌───────────┴────────────┐
                              ▼                        ▼
                        Extract Sections         Extract Tables/Equations
                              │                        │
                              ▼                        ▼
                    Store in paper_sections   Store in paper_tables/equations
                              │                        │
                              └───────────┬────────────┘
                                          ▼
                              Mark paper.is_processed = TRUE
                                          │
                                          ▼
                              Ready for ANY user to retrieve!
```

### Trigger Locations
| Trigger | File | When |
|---------|------|------|
| Save to library | `user_service.py` | `save_paper()` → `_trigger_pdf_processing_if_needed()` |
| Upload PDF | `upload_async.py` | After paper created |
| Manual API | `pdf.py` | POST `/api/v1/pdf/process` |

---

## ✅ Bug Fixes Completed

| Issue | Status | Fix Location |
|-------|--------|--------------|
| RAG Engine never initialized | ✅ FIXED | `agent_service.py` - now initializes RAGEngine |
| Async/Sync DB mismatch | ✅ FIXED | `database_tools.py` - all functions now sync |
| Missing tools in orchestrator | ✅ FIXED | `orchestrator.py` - added update_methodology, update_synthesis |
| Frontend selectedPaperIds type | ✅ FIXED | `AIAssistant.tsx` - parseInt() conversion |
| User ID key inconsistency | ✅ FIXED | `AIAssistant.tsx` - both keys checked |
| Too strict loop detection | ✅ FIXED | `base.py` - tracks action+params hash |

---

## 📊 Project Statistics

| Category | Count |
|----------|-------|
| API Routers | 16 |
| API Endpoints | ~55+ |
| Frontend Components | 87 |
| React Hooks | 9 |
| Database Tables | 46 |
| Agent Tools | 21 |
| Test Files | 35 |

---

## 🗂️ Key Files Reference

### Backend Core
| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app + router registration |
| `app/core/rag_engine.py` | LlamaIndex + Docling integration |
| `app/core/pdf_extractor.py` | PDF → sections/tables/equations extraction |
| `app/agents/orchestrator.py` | Agent with 21 tools |
| `app/agents/base.py` | FlexibleAgent ReAct implementation |
| `app/services/agent_service.py` | Conversation management |
| `app/services/user_service.py` | User library + auto PDF trigger |

### Backend Tools
| File | Purpose |
|------|---------|
| `app/tools/database_tools.py` | Project/comparison/findings CRUD |
| `app/tools/literature_tools.py` | Paper sections/summary read/write |
| `app/tools/rag_tools.py` | Semantic search + compare |
| `app/tools/pdf_tools.py` | PDF parsing jobs |

### API Endpoints
| File | Purpose |
|------|---------|
| `app/api/v1/agent.py` | Chat REST + WebSocket |
| `app/api/v1/pdf.py` | PDF processing endpoints |
| `app/api/v1/papers.py` | Paper search + management |
| `app/api/v1/users.py` | User library + notes |
| `app/api/v1/upload_async.py` | PDF upload with processing |

### Frontend Core
| File | Purpose |
|------|---------|
| `src/components/workspace/AIAssistant.tsx` | Chat UI + WebSocket |
| `src/hooks/useUser.ts` | User session management |
| `src/api/client.ts` | Axios with X-User-ID header |
