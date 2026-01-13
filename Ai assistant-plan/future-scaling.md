# Future Scaling & Improvements Roadmap

A living document for future enhancements across all system aspects.

---

## Table of Contents
1. [Database & Storage Scaling](#1-database--storage-scaling)
2. [Vector Search Improvements](#2-vector-search-improvements)
3. [Memory System Enhancements](#3-memory-system-enhancements)
4. [RAG Pipeline Improvements](#4-rag-pipeline-improvements)
5. [Agent System Enhancements](#5-agent-system-enhancements)
6. [LLM Optimization](#6-llm-optimization)
7. [Infrastructure & DevOps](#7-infrastructure--devops)
8. [Monitoring & Observability](#8-monitoring--observability)
9. [Cost Optimization](#9-cost-optimization)
10. [Security Hardening](#10-security-hardening)

---

## 1. Database & Storage Scaling

### Current State
- PostgreSQL with pgvector
- All data in single database
- ~25 tables

### Future Improvements

| Priority | Improvement | When to Implement | Complexity |
|----------|-------------|-------------------|------------|
| 🟡 Medium | **Table Partitioning** | >10K users | Medium |
| 🟡 Medium | **Read Replicas** | High read load | Medium |
| 🔴 High Scale | **Database Sharding** | >1M users | High |
| 🔴 High Scale | **Separate Vector DB** | >10M vectors | High |

### Repository Pattern for DB Abstraction
```python
# Future: Abstract database access
class BaseRepository(ABC):
    @abstractmethod
    async def create(self, entity): ...
    @abstractmethod
    async def find_by_id(self, id): ...
    
class PostgresRepository(BaseRepository): ...  # Current
class MongoRepository(BaseRepository): ...     # Future option
```

### Cold Storage
- Move old papers/conversations to S3
- Keep hot data in PostgreSQL
- Lazy load on access

---

## 2. Vector Search Improvements

### Current State
- pgvector (768-dim Nomic embeddings)
- IVFFlat index
- ~10K vectors capacity efficient

### Migration Options

| Vector DB | When to Switch | Estimated Cost |
|-----------|----------------|----------------|
| **Pinecone** | >100K vectors, need managed | $70/month starter |
| **Qdrant** | Want open source, self-host | Free (server cost) |
| **Weaviate** | Need hybrid search focus | Free tier available |
| **Milvus** | Enterprise, >1B vectors | Enterprise pricing |

### Index Improvements
```sql
-- Current: IVFFlat (fast build, good accuracy)
CREATE INDEX USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Future: HNSW (slower build, better accuracy)
CREATE INDEX USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

### Hybrid Search Enhancement
- Current: Vector + BM25 (LlamaIndex QueryFusionRetriever)
- Future: Add ColBERT for late interaction scoring

---

## 3. Memory System Enhancements

### Current State
- Flat memory storage
- Similarity deduplication (0.9 threshold)
- Importance score decay

### Advanced Techniques to Add

#### 3.1 Memory Compression (Summarization)
```python
# Group similar memories → Summarize into one
memories = [
    "User researches ML",
    "User interested in machine learning",
    "User works on ML for robotics"
]
compressed = "User researches ML, particularly for robotics applications"
```

#### 3.2 Hierarchical Memory
```
LONG-TERM (permanent, high importance)
├── "User is a PhD student in CS"
├── "Focuses on NLP research"
│
SHORT-TERM (session-based, expires in 7 days)
├── "Currently comparing transformer models"
│
WORKING (current conversation only)
└── "Asked about BERT vs GPT"
```

#### 3.3 Memory Consolidation (Sleep-like)
- Run nightly job to:
  - Merge similar memories
  - Delete low-importance old memories
  - Promote frequently accessed to long-term

#### 3.4 Contextual Retrieval (Anthropic Pattern)
```python
# Before storing chunks, add document context
original = "The accuracy was 95%"
contextualized = "[Paper: Transformer Efficiency Study] The accuracy was 95%"
# Improves retrieval relevance by 49%
```

---

## 4. RAG Pipeline Improvements

### Current State
- Nomic embeddings (768 dims)
- Section-level chunking
- Hybrid search (Vector + BM25)

### Planned Improvements

#### 4.1 Re-ranking Layer
```python
# After initial retrieval, re-rank with cross-encoder
from sentence_transformers import CrossEncoder
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Top 50 from vector search → Re-rank → Top 10
candidates = vector_search(query, top_k=50)
scores = reranker.predict([(query, c.text) for c in candidates])
final = sorted(zip(scores, candidates), reverse=True)[:10]
```

#### 4.2 Query Expansion
```python
# Generate multiple query variations
original = "machine learning methods"
expanded = [
    "machine learning methods",
    "ML techniques and approaches",
    "artificial intelligence algorithms",
    "deep learning methodologies"
]
# Search with all, merge results
```

#### 4.3 Agentic RAG
```python
# Let agent decide retrieval strategy
if query_type == "comparison":
    # Retrieve from multiple papers, side by side
elif query_type == "deep_dive":
    # Retrieve all sections of one paper
elif query_type == "overview":
    # Retrieve abstracts only
```

#### 4.4 Citation Tracking
- Track which chunks were used in responses
- Build citation graph
- Improve future retrieval based on usage

---

## 5. Agent System Enhancements

### Current State
- MainAgent (router, 5 tools)
- LiteratureReviewAgent (specialist, 6 modes)
- Custom ReAct implementation

### Future Improvements

#### 5.1 More Specialized Agents
```
MainAgent (router)
├── LiteratureReviewAgent (current)
├── WritingAgent (future) - Help write papers
├── AnalysisAgent (future) - Statistical analysis
└── CitationAgent (future) - Citation management
```

#### 5.2 Agent Learning
- Store successful tool sequences
- Suggest tool chains for similar queries
- Learn user preferences per agent

#### 5.3 Parallel Tool Execution
```python
# Current: Sequential
result1 = await tool1()
result2 = await tool2()  # Waits for tool1

# Future: Parallel when independent
results = await asyncio.gather(tool1(), tool2())
```

#### 5.4 Planning Before Acting
```python
# Add explicit planning phase
plan = await agent.plan(query)  # "I will: 1) search, 2) compare, 3) write"
user_approval = await get_approval(plan)
if user_approval:
    result = await agent.execute(plan)
```

---

## 6. LLM Optimization

### Current State
- Groq (qwen/qwen3-32b)
- Single model for all tasks

### Improvements

#### 6.1 Model Routing
```python
# Use smaller models for simple tasks
if task_type == "classification":
    model = "qwen/qwen-7b"  # Fast, cheap
elif task_type == "extraction":
    model = "qwen/qwen3-32b"  # Current
elif task_type == "complex_reasoning":
    model = "gpt-4"  # Fallback for hard tasks
```

#### 6.2 Caching
- Cache identical prompts (Redis)
- Cache similar prompts (semantic cache)
- Cache tool results (already have @cached_tool)

#### 6.3 Streaming Optimization
- Stream tokens to UI faster
- Cancel generation if user navigates away

#### 6.4 Local Models (Cost Reduction)
- Run Qwen-7B locally for simple tasks
- Use API only for complex tasks

---

## 7. Infrastructure & DevOps

### Current State
- Local development
- Manual deployment

### Future Improvements

| Priority | Improvement | Benefit |
|----------|-------------|---------|
| 🟢 Soon | Docker Compose | Easy local setup |
| 🟢 Soon | CI/CD Pipeline | Automated testing |
| 🟡 Medium | Kubernetes | Horizontal scaling |
| 🟡 Medium | Auto-scaling | Cost optimization |
| 🔴 Scale | Multi-region | Global latency |

### Docker Compose Example
```yaml
services:
  backend:
    build: ./backend
    depends_on: [postgres, redis]
  postgres:
    image: pgvector/pgvector:pg16
  redis:
    image: redis:alpine
  celery:
    build: ./backend
    command: celery -A app.worker worker
```

---

## 8. Monitoring & Observability

### Current State
- OpenTelemetry tracing (basic)
- LLM usage logs in database

### Improvements

#### 8.1 Dashboards
- Grafana dashboard for:
  - LLM token usage per user
  - RAG latency percentiles
  - Agent success/failure rates

#### 8.2 Alerting
- Alert on: High error rate, slow queries, quota limits

#### 8.3 LLM-Specific Monitoring
- Track hallucination rate (validation failures)
- Track tool call patterns
- A/B test prompts

---

## 9. Cost Optimization

### Current Costs (Estimated)
| Component | Current | Optimized |
|-----------|---------|-----------|
| LLM (Groq) | ~$X/month | -50% with caching |
| Embeddings | ~$Y/month | Free if local |
| Database | ~$Z/month | Same |

### Optimization Strategies
1. **Semantic Caching**: Cache similar queries
2. **Smaller Models**: Use 7B for simple tasks
3. **Local Embeddings**: Already using Nomic locally
4. **Lazy Loading**: Don't embed until needed
5. **Batch Processing**: Batch LLM calls when possible

---

## 10. Security Hardening

### Current State
- Backend-injected user_id
- Database-level user isolation

### Future Improvements

| Priority | Improvement | Status |
|----------|-------------|--------|
| 🟢 Soon | Rate limiting | Phase 5 |
| 🟢 Soon | Input sanitization | TODO |
| 🟡 Medium | Audit logging | Partial (data_change_history) |
| 🟡 Medium | Encryption at rest | Database level |
| 🔴 Important | Prompt injection defense | TODO |

### Prompt Injection Defense
```python
# Sanitize user input before passing to LLM
def sanitize_input(text: str) -> str:
    # Remove system-like prompts
    dangerous = ["ignore previous", "system:", "assistant:"]
    for d in dangerous:
        text = text.replace(d, "")
    return text
```

---

## Quick Reference: Implementation Priority

### Phase A: Now (Stability)
- [x] Database tables
- [x] Pydantic validation
- [x] Multi-agent architecture
- [x] Memory system
- [ ] Rate limiting (Phase 5)
- [ ] Basic caching (Phase 5)

### Phase B: Soon (Performance)
- [ ] Re-ranking layer
- [ ] Query expansion
- [ ] Semantic caching
- [ ] Docker Compose

### Phase C: Scale (Growth)
- [ ] Repository pattern for DB abstraction
- [ ] Memory compression
- [ ] Model routing
- [ ] Kubernetes deployment

### Phase D: Enterprise (Large Scale)
- [ ] Separate vector database
- [ ] Multi-region deployment
- [ ] Advanced security
- [ ] Custom fine-tuned models

---

## Notes & Ideas

_Add your thoughts here as you work on the system:_

- 
- 
- 
