# 📡 API Reference Documentation

**Base URL**: `http://localhost:8000/api/v1`

This document details all available API endpoints, their parameters, and response structures, automatically verified from the source code.

---

## 📚 Papers API (`/papers`)

### Search Papers
**`GET /papers/search`**
Performs an intelligent hybrid search across local database and external APIs.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search terms (2-500 chars) |
| `category` | string | Yes | Research category ID (e.g., `ai_cs`) |
| `mode` | string | Yes | `auto`, `quick`, or `ai` |
| `limit` | int | No | Max results (default 100) |

**Response:**
```json
{
  "papers": [
    {
      "id": 1,
      "title": "Deep Learning... ",
      "abstract": "...",
      "authors": ["LeCun", "Hinton"],
      "publication_date": "2023-01-01",
      "source": "arxiv",
      "citation_count": 500,
      "venue": "Nature",
      "pdf_url": "http://..."
    }
  ],
  "total": 100,
  "metadata": {
    "search_time": 1.2,
    "sources_used": ["local_db", "arxiv"]
  }
}
```

### AI Suggestions
**`POST /papers/ai-suggestions`**
Generates smart search queries based on a problem statement.

**Body:**
- `problem_statement` (str): Detailed description
- `goals` (str, optional): Research goals
- `category` (str, optional): Context category

### Fetch by DOI
**`POST /papers/fetch-by-doi`**
Directly imports a paper using its DOI.

**Body:**
- `doi` (str): e.g., "10.1038/nature12373"
- `category` (str, optional)

### Categories
**`GET /papers/categories`**
Returns configured search categories (AI, Medicine, etc.) and their sources.

### Statistics
**`GET /papers/stats`**
Returns total paper counts and breakdown by source.

### Health Check
**`GET /papers/health`**
Checks status of Redis and external API adapters.

### Embeddings
- **`POST /papers/embeddings/generate`**: Trigger enhanced embedding generation.
- **`POST /papers/embeddings/regenerate`**: Upgrade legacy embeddings.
- **`GET /papers/embeddings/stats`**: View embedding coverage and versions.

---

## 👤 Users API (`/users`)

### Initialization
**`POST /users/init`**
Initialize or retrieve a local user session (UUID).

### Saved Papers
- **`POST /users/saved-papers`**: Save a paper.
    - Body: `{ "paper_id": 123, "tags": [], "personal_notes": "..." }`
- **`GET /users/saved-papers`**: List all saved papers.
- **`DELETE /users/saved-papers/{paper_id}`**: Unsave a paper.
- **`GET /users/saved-papers/{paper_id}/check`**: Check if saved.

### Notes & Folders
- **`POST /users/notes`**: Create a note.
- **`GET /users/notes`**: List notes (optional `paper_id` filter).
- **`PUT /users/notes/{note_id}`**: Update note content.
- **`DELETE /users/notes/{note_id}`**: Delete note.
- **`POST /users/notes/folder`**: Create a folder.
- **`PATCH /users/notes/{item_id}/rename`**: Rename folder/note.
- **`PATCH /users/notes/{item_id}/move`**: Move folder/note.

### Literature Reviews
- **`POST /users/literature-reviews`**: Create a new review project.
- **`GET /users/literature-reviews`**: List projects.
- **`PUT /users/literature-reviews/{id}`**: Update project.
- **`DELETE /users/literature-reviews/{id}`**: Delete project.
- **`POST /users/literature-reviews/{id}/seed`**: Fill with demo data.

### Statistics
**`GET /users/stats`**
Returns counts of saved papers, notes, reviews, and search history.

---

## 🕒 Search History API (`/search-history`)

- **`POST /search-history/save`**: Manually save a search query.
- **`GET /search-history/list`**: Get recent history.
- **`DELETE /search-history/clear`**: Clear all history.
- **`DELETE /search-history/{id}`**: Delete specific entry.

---

## ⚖️ Comparison API (`/comparison`)

Endpoints for the "Compare Papers" feature.

- **`GET /projects/{id}/comparison/config`**: Get selected papers for comparison.
- **`PUT /projects/{id}/comparison/config`**: Update selection.
- **`GET /projects/{id}/comparison/attributes`**: Get comparison matrix data.
- **`PATCH /projects/{id}/comparison/attributes/{paper_id}`**: Update specific cell/attribute.
