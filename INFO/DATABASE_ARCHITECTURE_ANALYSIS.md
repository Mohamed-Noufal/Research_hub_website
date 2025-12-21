# 🗄️ Database Architecture Analysis

**System**: PostgreSQL with `pgvector` extension.
**ORM**: SQLAlchemy.

## 🏗️ Core Tables

### 1. `papers`
The central repository for research papers.
- **`id`** (Integer, PK): Unique ID.
- **`title`** (String): Title of the paper.
- **`abstract`** (Text): Full abstract.
- **`authors`** (JSON): List of author names.
- **`publication_date`** (DateTime): Date of publication.
- **`source`** (String): `arxiv`, `semantic_scholar`, `openalex`, etc.
- **`category`** (String): Domain category (e.g., `ai_cs`).
- **`citation_count`** (Integer).
- **`pdf_url`** (String).
- **`venue`** (String).
- **`embedding`** (Vector(768)): Semantic embedding for search (Nomic Embed Text v1.5).
- **`is_processed`** (Boolean): Embedding generation status.
- **`paper_metadata`** (JSONB): Flex storage.
- **indexes**: `id`, `arxiv_id`, `doi`, `openalex_id`, `semantic_scholar_id`.

### 2. `local_users`
Session-based user management (no auth).
- **`id`** (UUID, PK): User ID.
- **`created_at`, `last_active`** (DateTime).

### 3. `user_saved_papers`
Join table for User <-> Paper (Library).
- **`user_id`**, **`paper_id`** (FKs).
- **`tags`** (Array): User tags.
- **`personal_notes`** (Text).
- **`read_status`** (String): `read`, `reading`, `unread`.

### 4. `user_notes`
Hierarchical note storage.
- **`id`** (PK).
- **`user_id`**, **`paper_id`** (Optional).
- **`title`**, **`content`**.
- **`parent_id`** (FK): For folder structure (Self-referential).
- **`is_folder`** (Boolean).
- **`path`** (String): Materialized path for fast tree traversal.

### 5. `user_search_history`
- **`user_id`** (FK).
- **`query`**, **`category`**.
- **`results_count`**.

## 🔬 Literature Review & Analysis Tables (Phase 2 & 3)

### `user_literature_reviews`
Groups papers into projects.
- **`status`**, **`title`**, **`description`**.
- **`paper_ids`** (Array[Integer]).

### `literature_review_annotations`
Specific notes on papers within a review.
- **`methodology`**, **`sample_size`**.
- **`key_findings`**, **`limitations`**.

### `literature_review_findings`
Synthesized findings across papers.
- **`description`**, **`evidence_level`**.

### `paper_comparisons`
Stores comparison matrix configurations.
- **`project_id`**.
- **`comparison_data`** (JSON).

### `comparison_configs` & `comparison_attributes`
(Direct SQL access in `comparison.py` implies these might be dynamic or raw tables).
- Stores the state of the "Compare" tab grid (selected papers, manually entered attributes per paper).

### `ai_synthesis`
Stores AI-generated content.
- **`ai_prompt`**, **`ai_response`**.
- **`synthesis_type`** (summary, gap_analysis).

## 🚀 Optimization Strategy
- **Bulk Inserts**: Uses `db.bulk_insert_mappings` for high-throughput paper saving.
- **Background Tasks**: Embeddings are generated post-request to ensure <15s API latency.
- **Vector Search**: `pgvector` with cosine similarity (`<=>`).
