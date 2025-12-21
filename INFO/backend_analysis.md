# Backend Analysis & Architecture

## Overview
The backend is built using **FastAPI**, a high-performance Python web framework. It serves as the core logic layer, handling API requests, interacting with the PostgreSQL database, and managing external searches (arXiv, Semantic Scholar, OpenAlex).

**Location:** `backend/app/main.py` serves as the entry point.

## 📂 Key Files
- **Entry Point**: `backend/app/main.py`
- **Database Setup**: `backend/app/core/database.py`
- **Models**: `backend/app/models/`
- **Services**: `backend/app/services/`

## 📡 API Endpoints

The API is versioned (e.g., `/api/v1`) and organized into several routers.

### 1. Papers API (`/api/v1/papers`)
Handles paper search and retrieval.
- **`GET /search`**: The main search endpoint. It accepts a `query`, `category` (e.g., `ai_cs`), and `mode`.
    - **Logic**: 
        1. Checks local **Redis cache** for identical queries (`unified_search_service.py`).
        2. **Parallel Execution**: Simultaneously searches the local database (PostgreSQL with pgvector) and external APIs using `asyncio.gather`.
        3. **Logic**: `app.services.unified_search_service.UnifiedSearchService._normal_search_flow` orchestrates this.
        4. **Background Tasks**: Uses FastAPI `BackgroundTasks` to:
            - Save new papers via **Bulk Insert** (`db.bulk_insert_mappings`).
            - Generate embeddings for new papers in the background (post-response).
    - **Performance**: Designed for 10-15s response time with ongoing background embedding generation.
- **`POST /ai-suggestions`**: Uses `AIQueryAnalyzer` to generate 3-5 search queries based on a problem statement.
- **`GET /categories`**: Returns hardcoded category configurations (e.g., `ai_cs` maps to arXiv, Semantic Scholar, OpenAlex).
- **`GET /stats`**: Returns system statistics (total papers, source breakdown).

### 2. Users API (`/api/v1/users`)
Manages user sessions and personal libraries.
- **`POST /init`**: Initializes a new session-based user (returns a UUID).
- **`POST /saved-papers`**: Saves a paper to the user's library.
- **`GET /saved-papers`**: Retrieves the user's saved papers.
- **`DELETE /saved-papers/{id}`**: Removes a paper from the library.
- **`POST /notes`**: Creates a note attached to a paper.

### 3. Literature Reviews API (`/api/v1/users/literature-reviews`)
Manages comprehensive literature review projects.
- **`POST /`**: Create a new literature review project.
- **`GET /`**: List user's reviews.
- **`PUT /{id}`**: Update review details.

### 4. Advanced Analysis APIs
- **`/comparison`**: Endpoints for comparing multiple papers (methodology, results).
- **`/synthesis`**: AI-driven synthesis of multiple papers.
- **`/findings`**: Extracting key findings from papers.
- **`/analysis`**: Advanced analytics and grouping of papers.

## 🔗 Connections & Integrations

### 1. Database Connection
- **ORM**: Uses **SQLAlchemy** for database interactions.
- **Database**: **PostgreSQL** with `pgvector` extension.
- **Connection String**: Loaded from `.env` settings.
- **Session Management**: Each request gets a dedicated database session (`get_db` dependency).

### 2. Redis Cache
- Used for caching search results to reduce latency and external API rate limits.
- **Key Format**: `search:{query}:{category}`.

### 3. External APIs
- **arXiv**: Fetches physics, CS, and math papers.
- **Semantic Scholar**: Fetches broad scientific papers.
- **OpenAlex**: Fallback metadata source.

### 4. Vector Search
- **Service**: `EnhancedVectorService`
- **Embedding Model**: Papers are passed through an embedding model (e.g., `nomic-embed-text`).
- **Storage**: Embeddings are stored in the `papers` table `embedding` column.
- **Search**: Uses cosine distance (`<=>` operator) for semantic search.
- **Batching**: Embeddings are generated in batches of 100 to optimize throughput.

## 🔄 Data Flow Example (Search)
1. **Frontend** sends `GET /search?query=transformer`.
2. **FastAPI** `papers.router` receives request.
3. **Service Layer** (`UnifiedSearchService`) checks Redis cache.
4. **Parallel Execution**:
    - **Local**: Queries PostgreSQL for vector similarity + keyword match (Hybrid Search).
    - **External**: Calls APIs based on category (e.g., `ai_cs` -> arXiv, Semantic Scholar).
5. **Merge**: Results are merged, with deduplication logic preferring local/richer metadata.
6. **Response**: JSON returned to user immediately.
7. **Background**: New papers are bulk-inserted and queued for embedding generation.
