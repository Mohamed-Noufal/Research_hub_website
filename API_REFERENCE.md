# 📡 API Reference - ResearchHub

**Quick reference for all API endpoints**

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently using session-based authentication with a default test user. JWT authentication coming soon.

---

## 📝 Endpoints

### Papers API

#### Search Papers

```http
GET /papers/search
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | Search query (2-500 chars) |
| category | string | Yes | - | Research category ID |
| mode | string | Yes | - | 'normal' or 'ai' |
| limit | number | No | 100 | Max results (1-100) |

**Example:**
```bash
curl "http://localhost:8000/api/v1/papers/search?query=neural%20networks&category=ai_cs&mode=ai&limit=20"
```

**Response:**
```json
{
  "papers": [
    {
      "id": "1",
      "title": "Paper Title",
      "abstract": "Paper abstract...",
      "authors": ["Author 1", "Author 2"],
      "publication_date": "2024-01-15",
      "source": "arxiv",
      "doi": "10.1234/example",
      "citation_count": 42,
      "category": "cs.AI",
      "venue": "NeurIPS 2024",
      "pdf_url": "https://arxiv.org/pdf/..."
    }
  ],
  "total": 156,
  "metadata": {
    "search_time": 1.23,
    "sources_used": ["arxiv", "semantic_scholar"],
    "mode": "ai"
  }
}
```

---

#### Get Categories

```http
GET /papers/categories
```

**Example:**
```bash
curl http://localhost:8000/api/v1/papers/categories
```

**Response:**
```json
{
  "categories": {
    "ai_cs": {
      "id": "ai_cs",
      "name": "AI & Computer Science",
      "description": "Machine learning, AI, computer vision, NLP",
      "sources": ["arxiv", "semantic_scholar", "openalex"],
      "source_count": 3
    },
    "medicine_biology": {
      "id": "medicine_biology",
      "name": "Medicine & Biology",
      "description": "Clinical research, biomedical, healthcare",
      "sources": ["pubmed", "europe_pmc", "crossref"],
      "source_count": 3
    }
  },
  "total": 6
}
```

---

#### Health Check

```http
GET /papers/health
```

**Example:**
```bash
curl http://localhost:8000/api/v1/papers/health
```

**Response:**
```json
{
  "status": "healthy",
  "redis_connected": true,
  "services": {
    "arxiv": "operational",
    "semantic_scholar": "operational",
    "openalex": "operational"
  }
}
```

---

#### Get Stats

```http
GET /papers/stats
```

**Example:**
```bash
curl http://localhost:8000/api/v1/papers/stats
```

**Response:**
```json
{
  "total_papers": 15423,
  "by_source": {
    "arxiv": 8521,
    "semantic_scholar": 4231,
    "openalex": 2671
  },
  "processed_papers": 14892
}
```

---

### Users API

#### Initialize User

```http
POST /users/init
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/users/init
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success"
}
```

---

#### Get User Stats

```http
GET /users/stats
```

**Example:**
```bash
curl http://localhost:8000/api/v1/users/stats
```

**Response:**
```json
{
  "saved_papers": 42,
  "notes": 128,
  "literature_reviews": 5,
  "total_searches": 256
}
```

---

#### Save Paper

```http
POST /users/saved-papers
```

**Body:**
```json
{
  "paper_id": 123,
  "tags": ["machine-learning", "nlp"],
  "personal_notes": "Interesting approach to transformers"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/users/saved-papers \
  -H "Content-Type: application/json" \
  -d '{"paper_id": 123, "tags": ["ml"], "personal_notes": "Great paper"}'
```

**Response:**
```json
{
  "id": 456,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "paper_id": 123,
  "tags": ["machine-learning", "nlp"],
  "personal_notes": "Interesting approach to transformers",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### Get Saved Papers

```http
GET /users/saved-papers
```

**Example:**
```bash
curl http://localhost:8000/api/v1/users/saved-papers
```

**Response:**
```json
{
  "papers": [
    {
      "id": "123",
      "title": "Paper Title",
      "authors": ["Author 1"],
      "saved_at": "2024-01-15T10:30:00Z",
      "tags": ["ml", "nlp"],
      "personal_notes": "Important paper"
    }
  ],
  "total": 42
}
```

---

#### Unsave Paper

```http
DELETE /users/saved-papers/{paper_id}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/users/saved-papers/123
```

**Response:**
```json
{
  "status": "removed"
}
```

---

#### Check if Paper is Saved

```http
GET /users/saved-papers/{paper_id}/check
```

**Example:**
```bash
curl http://localhost:8000/api/v1/users/saved-papers/123/check
```

**Response:**
```json
{
  "is_saved": true
}
```

---

### Notes API

#### Create Note

```http
POST /users/notes
```

**Body:**
```json
{
  "paper_id": 123,
  "title": "Research Notes",
  "content": "# Important Findings\n\n- Finding 1\n- Finding 2",
  "content_type": "markdown"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/users/notes \
  -H "Content-Type: application/json" \
  -d '{"paper_id": 123, "title": "Notes", "content": "My notes", "content_type": "markdown"}'
```

**Response:**
```json
{
  "id": 789,
  "paper_id": 123,
  "title": "Research Notes",
  "content": "# Important Findings...",
  "content_type": "markdown",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### Get Notes

```http
GET /users/notes?paper_id={paper_id}
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| paper_id | number | No | Filter by paper ID |

**Example:**
```bash
curl "http://localhost:8000/api/v1/users/notes?paper_id=123"
```

**Response:**
```json
{
  "notes": [
    {
      "id": 789,
      "paper_id": 123,
      "title": "Research Notes",
      "content": "My notes...",
      "content_type": "markdown",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

#### Update Note

```http
PUT /users/notes/{note_id}
```

**Body:**
```json
{
  "title": "Updated Title",
  "content": "Updated content"
}
```

**Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/users/notes/789 \
  -H "Content-Type: application/json" \
  -d '{"title": "New Title", "content": "New content"}'
```

**Response:**
```json
{
  "status": "updated"
}
```

---

#### Delete Note

```http
DELETE /users/notes/{note_id}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/users/notes/789
```

**Response:**
```json
{
  "status": "deleted"
}
```

---

### Literature Reviews API

#### Create Literature Review

```http
POST /users/literature-reviews
```

**Body:**
```json
{
  "title": "Survey on Neural Networks",
  "description": "Comprehensive review of neural network architectures",
  "paper_ids": [123, 456, 789]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/users/literature-reviews \
  -H "Content-Type: application/json" \
  -d '{"title": "My Review", "description": "Review description", "paper_ids": [123, 456]}'
```

**Response:**
```json
{
  "id": 101,
  "title": "Survey on Neural Networks",
  "description": "Comprehensive review...",
  "paper_ids": [123, 456, 789],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### Get Literature Reviews

```http
GET /users/literature-reviews
```

**Example:**
```bash
curl http://localhost:8000/api/v1/users/literature-reviews
```

**Response:**
```json
{
  "reviews": [
    {
      "id": 101,
      "title": "Survey on Neural Networks",
      "description": "Comprehensive review...",
      "paper_ids": [123, 456, 789],
      "paper_count": 3,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 5
}
```

---

#### Update Literature Review

```http
PUT /users/literature-reviews/{review_id}
```

**Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "paper_ids": [123, 456, 789, 111]
}
```

**Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/users/literature-reviews/101 \
  -H "Content-Type: application/json" \
  -d '{"title": "New Title"}'
```

**Response:**
```json
{
  "status": "updated"
}
```

---

#### Delete Literature Review

```http
DELETE /users/literature-reviews/{review_id}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/users/literature-reviews/101
```

**Response:**
```json
{
  "status": "deleted"
}
```

---

#### Get Search History

```http
GET /users/search-history?limit={limit}
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | number | No | 50 | Max history items |

**Example:**
```bash
curl "http://localhost:8000/api/v1/users/search-history?limit=20"
```

**Response:**
```json
{
  "history": [
    {
      "id": 321,
      "query": "neural networks",
      "category": "ai_cs",
      "results_count": 156,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 256
}
```

---

## 🔄 Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `500` - Internal Server Error

---

## 🧪 Testing with curl

### Complete Workflow Example

```bash
# 1. Initialize user
curl -X POST http://localhost:8000/api/v1/users/init

# 2. Get categories
curl http://localhost:8000/api/v1/papers/categories

# 3. Search for papers
curl "http://localhost:8000/api/v1/papers/search?query=machine%20learning&category=ai_cs&mode=ai&limit=10"

# 4. Save a paper (use paper_id from search results)
curl -X POST http://localhost:8000/api/v1/users/saved-papers \
  -H "Content-Type: application/json" \
  -d '{"paper_id": 123}'

# 5. Get saved papers
curl http://localhost:8000/api/v1/users/saved-papers

# 6. Create a note
curl -X POST http://localhost:8000/api/v1/users/notes \
  -H "Content-Type: application/json" \
  -d '{"paper_id": 123, "title": "My Notes", "content": "Important findings"}'

# 7. Get user stats
curl http://localhost:8000/api/v1/users/stats
```

---

## 📚 Interactive Documentation

Visit the auto-generated API documentation at:

**Swagger UI:** `http://localhost:8000/docs`
**ReDoc:** `http://localhost:8000/redoc`

---

## 🔗 Frontend Integration

**TypeScript/JavaScript Example:**

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
});

// Search papers
const searchPapers = async (query: string, category: string) => {
  const response = await api.get('/papers/search', {
    params: { query, category, mode: 'ai', limit: 50 }
  });
  return response.data;
};

// Save paper
const savePaper = async (paperId: number) => {
  const response = await api.post('/users/saved-papers', {
    paper_id: paperId
  });
  return response.data;
};
```

---

**Made with ❤️ for the research community**
