# Backend Developer Guide

This document provides a comprehensive overview of the **Literature Review AI Assistant** backend. It is designed to help new developers understand the architecture, module responsibilities, and data flows immediately.

## 🏗️ High-Level Architecture

The system is built on **FastAPI** (Python 3.10+) and uses a hybrid architecture combining REST APIs, Celery background workers, and an Agentic AI system.

```mermaid
graph TD
    Client[Frontend (Next.js)] <--> API[FastAPI Backend]
    API <--> Services[Service Layer]
    
    subgraph Core Services
        Services <--> Search[Unified Search Service]
        Services <--> Agent[AI Agent Orchestrator]
        Services <--> RAG[RAG Engine (LlamaIndex)]
    end
    
    subgraph Data & processing
        Search <--> DB[(PostgreSQL + pgvector)]
        RAG <--> DB
        API --> Celery[Celery Workers]
        Celery --> Redis[Redis Broker]
        Celery --> Extractor[Docling PDF Extractor]
    end
    
    subgraph External
        Search --> EXT[Arxiv / Semantic Scholar / OpenAlex]
        Agent --> LLM[Groq (Qwen3-32B) / OpenAI]
    end
```

---

## 📂 Project Structure

```text
backend/app/
├── api/v1/                 # REST API Endpoints
│   ├── papers_core.py      # Main search, stats, health checks
│   ├── papers_embeddings.py# Vector embedding management
│   ├── papers_pdf.py       # PDF upload/download & processing trigger
│   ├── papers_doi.py       # DOI import logic
│   └── papers_manual.py    # Manual paper entry
├── agents/                 # AI Agent System
│   ├── orchestrator.py     # Main agent controller (entry point)
│   ├── base.py             # ReAct loop implementation (FlexibleAgent)
│   └── literature_agent.py # Specialized literature tools
├── core/                   # Core Infrastructure
│   ├── database.py         # SQLAlchemy setup
│   ├── config.py           # Environment variables
│   ├── rag_engine.py       # LlamaIndex retrieval logic
│   ├── memory.py           # Short-term agent memory
│   └── memory_manager.py   # Long-term user memory (Mem0-style)
├── models/                 # SQLAlchemy Database Models
│   ├── paper.py            # Papers & Sections
│   └── agent.py            # Conversations & Messages
├── services/               # Business Logic Layer
│   ├── unified_search_service.py # Hybrid Search (Local + External)
│   └── pdf_extractor.py    # Docling integration
├── tools/                  # Agent Tools
│   ├── database_tools.py   # DB read/write tools
│   ├── rag_tools.py        # Semantic search & Extraction tools
│   └── master_tools.py     # Complex workflows (e.g., "fill all tabs")
└── workers/                # Background Tasks
    └── tasks.py            # Celery task definitions
```

---

## 🧩 Key Modules Explained

### 1. Unified Search System (`unified_search_service.py`)
*   **Hybrid Search**: Combines **Keyword Search** (Postgres `tsvector`) and **Semantic Search** (pgvector cosine similarity).
*   **External Integration**: Fetches from Arxiv, Semantic Scholar, and OpenAlex in parallel.
*   **Auto-Learning**: Results from external APIs are automatically saved and embedded in the background, enriching the local vector database over time.

### 2. The AI Agent (`agents/`)
*   **Orchestrator**: The central brain. It receives user messages, manages context, and initializes the `FlexibleAgent`.
*   **ReAct Loop (`base.py`)**: Implements the **Think -> Act -> Observe** loop.
    *   **Streaming**: Streams "thinking" steps to the UI for better UX.
    *   **Active Context**: Automatically tracks which project/paper is being discussed to avoid redundant DB lookups.
    *   **Memory**: Uses `active_context` (short-term) and `MemoryManager` (long-term) to personalize responses.
*   **Tools**: Functions the agent can call.
    *   `rag_tools.py`: Extract methodology, findings, find gaps using RAG.
    *   `database_tools.py`: Query projects, lists papers.

### 3. RAG Engine (`core/rag_engine.py`)
*   **Ingestion**: PDFs are parsed using **Docling**. content is split into chunks (sections, tables, figures).
*   **Embeddings**: Uses `nomic-embed-text-v1.5` (768 dimensions) via Ollama or remote API.
*   **Retrieval**: LlamaIndex vector store retriever fetches relevant chunks for agent queries.

### 4. Papers Module Refactor
The massive `papers.py` was split for maintainability:
*   `papers_core`: Search & Basic CRUD.
*   `papers_pdf`: File handling.
*   `papers_embeddings`: Vector generation triggers.
*   `papers_doi`: External import logic.
*   `papers_manual`: Form-based creation.

---

## 🔄 Data Flows

### Flow A: User Searches for a Paper
1.  **Request**: `GET /unified-search?query=transformers`
2.  **API**: `papers_core.py` calls `UnifiedSearchService`.
3.  **Service**:
    *   Checks Redis Cache.
    *   Runs **Parallel Search**:
        *   Local DB (Vector similarity).
        *   Arxiv/Semantic Scholar APIs.
    *   Merges results (deduplication).
4.  **Background**: New external papers are queued for embedding generation.
5.  **Response**: JSON list of papers.

### Flow B: AI Agent Extracts Methodology
1.  **Request**: User asks "Extract methodology for paper X".
2.  **Orchestrator**: Initializes `FlexibleAgent` with tools.
3.  **Think**: Agent decides to call `extract_methodology(paper_id=X)`.
4.  **Act (Tool)**: `rag_tools.py` -> `extract_methodology`.
    *   Fetches content from `paper_sections` table (preferred).
    *   Fallback: Uses RAG retrieval.
    *   Calls LLM (Qwen3) with a specific prompt.
    *   **Post-processing**: `strip_think_tags()` removes reasoning trace.
5.  **Observe**: Agent receives JSON data.
6.  **Final Answer**: Agent presents the extracted methodology.

---

## 💾 Database Schema (PostgreSQL)

*   `papers`: Core metadata (title, abstract, authors, date).
*   `paper_sections`: Parsed PDF content (introduction, methods, results).
*   `paper_figures` / `paper_tables`: Extracted visual elements.
*   `projects`: User-created collections of papers.
*   `agent_conversations`: Chat sessions.
*   `agent_messages`: Chat history.
*   `user_memories`: Long-term facts learned about the user.

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   PostgreSQL (with `pgvector` extension)
*   Redis
*   Node.js (for frontend)

### Environment Setup (`.env`)
```ini
DATABASE_URL=postgresql://user:pass@localhost:5432/research_db
OPENAI_API_KEY=sk-... (or GROQ_API_KEY)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
```

### Running the Backend
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run API Server (Hot-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Run Celery Worker (in separate terminal)
# Windows:
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
# Linux/Mac:
celery -A app.workers.celery_app worker --loglevel=info
```

---

## 🔌 API Endpoint Reference

The API is globally prefixed with `/api/v1`.

### 📄 Papers & Search (`/api/v1/papers`, `/api/v1/search-history`)

| Method | Path | Description | Parameters |
|:-------|:-----|:------------|:-----------|
| `GET` | `/papers/unified-search` | **Core Search**. Hybrid search (Vector + Keyword) across Local DB + External APIs. | `query`, `category`, `mode` |
| `GET` | `/papers/ai-suggestions` | AI analyzes query to suggest better keywords/topics. | `query`, `goals` |
| `GET` | `/papers/categories` | List available search categories. | None |
| `GET` | `/papers/stats` | Global database statistics. | None |
| `POST` | `/search-history/save` | Save a search query to history. | Body: `{"query": "...", "results_count": 10}` |
| `GET` | `/search-history/list` | Get user's search history. | Param: `limit` |
| `DELETE`| `/search-history/clear` | Clear all search history. | None |

### 📥 Ingestion & PDF (`/api/v1/papers`, `/api/v1/upload`, `/api/v1/pdf`)

| Method | Path | Description | Parameters |
|:-------|:-----|:------------|:-----------|
| `POST` | `/papers/manual` | **Manual Entry**. Create paper metadata. | Form: `title`, `authors`, `pdf_file` |
| `POST` | `/papers/fetch-by-doi` | **Smart Import**. Fetch metadata by DOI. | Body: `{"doi": "..."}` |
| `POST` | `/upload/async` | **Async Upload**. Upload PDF for background processing. | File: `file`, `project_id` |
| `GET` | `/upload/status/{task_id}`| Check status of async upload task. | Path: `task_id` |
| `POST` | `/pdf/process` | Trigger PDF extraction (sections/tables) manually. | Body: `{"paper_id": 123}` |
| `GET` | `/pdf/status/{paper_id}` | Check PDF extraction status/stats. | Path: `paper_id` |
| `POST` | `/papers/{id}/download-pdf`| Server-side download of specific URL. | Path: `id` |

### 👤 User, Projects & Library (`/api/v1/users`, `/api/v1/folders`)

| Method | Path | Description | Parameters |
|:-------|:-----|:------------|:-----------|
| `POST` | `/users/literature-reviews`| **Create Project**. | Body: `{"title": "..."}` |
| `GET` | `/users/literature-reviews`| List all projects. | None |
| `GET` | `/users/saved-papers` | Get user's personal library. | None |
| `POST` | `/users/saved-papers` | Save paper to library. | Body: `{"paper_id": 123}` |
| `POST` | `/users/notes` | Add note to paper. | Body: `{"paper_id": 123, "content": "..."}` |
| `GET` | `/folders` | List custom folders. | None |
| `POST` | `/folders` | Create folder. | Body: `{"name": "..."}` |
| `POST` | `/folders/{fid}/papers/{pid}`| Add paper to folder. | Path: `fid`, `pid` |

### � Analysis Tabs (`/api/v1/projects`)

These endpoints power the spreadsheet-like views in the frontend.

| Method | Path | Description | Parameters |
|:-------|:-----|:------------|:-----------|
| `GET` | `/{id}/papers` | **Enriched List**. Get papers with all extracted data (methodology, findings). | Path: `id` |
| `GET` | `/{id}/tables/{tab}/config`| Get table config (cols, visibility). | Path: `id`, `tab` |
| `PUT` | `/{id}/tables/{tab}/config`| Update table config. | Body: `{"columns": [...]}` |
| **Methodology** |
| `GET` | `/{id}/methodology` | Get methodology extraction data for all papers. | Path: `id` |
| `PATCH`| `/{id}/methodology/{pid}`| Update methodology fields. | Body: `{"methodology_description": "..."}` |
| **Findings & Gaps** |
| `GET` | `/{id}/findings` | Get findings data. | Path: `id` |
| `PATCH`| `/{id}/findings/{pid}` | Update findings. | Body: `{"key_finding": "..."}` |
| `GET` | `/{id}/gaps` | List research gaps. | Path: `id` |
| `POST` | `/{id}/gaps` | Create research gap. | Body: `{"description": "...", "priority": "High"}` |
| **Comparison** |
| `GET` | `/{id}/comparison/config` | Get comparison view config. | Path: `id` |
| `GET` | `/{id}/comparison/attributes`| Get detailed comparison matrix. | Path: `id` |
| `PATCH`| `/{id}/comparison/attributes/{pid}`| Update single cell in comparison. | Body: `{"attribute_name": "...", "value": "..."}` |
| **Synthesis** |
| `GET` | `/{id}/synthesis` | Get synthesis matrix (rows/cols/cells). | Path: `id` |
| `PUT` | `/{id}/synthesis/structure`| Update matrix structure (rows/cols). | Body: `{"rows": [...], "columns": [...]}` |
| `PATCH`| `/{id}/synthesis/cells` | Update single cell value. | Body: `{"row_id": "...", "col_id": "...", "value": "..."}` |

### � AI Agent (`/api/v1/agent`)

| Method | Path | Description | Parameters |
|:-------|:-----|:------------|:-----------|
| `POST` | `/chat` | **Single Turn**. Standard REST chat. | Body: `{"message": "..."}` |
| `WS` | `/ws/{conv_id}` | **Streaming**. WebSocket for ReAct stream. | Path: `conv_id` |
| `GET` | `/conversations` | List history. | Param: `limit` |
| `POST` | `/conversations` | Create new session. | Body: `{"title": "..."}` |

### 🧠 RAG & Admin (`/api/v1/knowledge-base`, `/api/v1/admin`)

| Method | Path | Description | Parameters |
|:-------|:-----|:------------|:-----------|
| `POST` | `projects/{id}/kb/add-papers`| Add papers to RAG index. | Body: `{"paper_ids": [...]}` |
| `GET` | `projects/{id}/kb/status` | Check embedding status. | Path: `id` |
| `GET` | `/admin/dashboard` | comprehensive system dashboard. | None |
| `GET` | `/admin/embedding-queue` | List papers waiting for embeddings. | None |
| `POST` | `/admin/trigger-embedding-generation` | Force start embedding worker. | Query: `max_papers` |
| `GET` | `/admin/data-quality-report` | Check for missing PDFs/Abstracts. | None |

---
