# Critical Issues & Fixes

## 🔴 Issue 1: Model Loading TWICE Every Search

**Problem:**
```
Load SentenceTransformer (6s)
Load SentenceTransformer AGAIN (6s)
= 12s wasted per search!
```

**Root Cause:** Model instantiated in `EnhancedVectorService.__init__()` for EVERY search

**Fix:** Cache model at startup in `main.py`

---

## 🔴 Issue 2: Embeddings NOT Being Generated

**Problem:**
```
✅ Found 0 papers in local database (EVERY search!)
📊 Queued embedding generation... (4 times!)
But embeddings never appear!
```

**Root Cause:** Celery tasks queued but not processed

**Check if Celery Worker Running:**
```bash
# Should show active worker
celery -A app.workers.celery_app inspect active
```

---

## 🔴 Issue 3: Manual Papers Not in Search

**Problem:** User manually added "Attention is all you need" but search doesn't find it

**Possible Causes:**
1. Paper has no embedding
2. Wrong category filter
3. Deduplication removing it

---

## ✅ Immediate Actions

### 1. Check Celery Worker Status
```python
# In backend directory
.venv\Scripts\python.exe -m celery -A app.workers.celery_app inspect active
```

### 2. Check Manual Paper
```sql
SELECT id, title, category, embedding IS NOT NULL as has_embedding
FROM papers 
WHERE title ILIKE '%attention is all you need%';
```

### 3. Generate Embeddings Directly (Skip Celery)
```python
# Run synchronously to test
python generate_embeddings_existing.py
```
