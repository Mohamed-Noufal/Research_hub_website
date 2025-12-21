# Cache and Database Search Issues - Root Cause Analysis

**Date:** 2025-11-22  
**Status:** 🔍 INVESTIGATING

---

## 🐛 **Issue #1: Cache Always Misses**

### **Symptoms:**
```
❌ Cache miss, performing search...
```
Every search, even for identical queries like "machine learning" × 2

### **Root Cause:**
The cache is using **in-memory cache**, not Redis:
```python
# Line 147 in unified_search_service.py
cached = await self.cache.get_search_results(query, limit=20, semantic_rerank=True)
```

**Problem:** In-memory cache is cleared on every server restart or reload!

### **Why It's Not Working:**
1. You're using `uvicorn --reload` which restarts on code changes
2. In-memory cache is lost on restart
3. No persistent Redis connection

### **Solution:**
Need to implement actual Redis caching or disable auto-reload during testing.

---

## 🐛 **Issue #2: Database Search Returns 0 Results**

### **Symptoms:**
```
🔍 Searching local embeddings for: 'machine learning' in category: ai_cs
✅ Found 0 papers in local database
```

Despite:
```
✅ Saved 20 new papers, updated 1040 existing papers with category 'ai_cs'
💾 Saving and embedding 20 papers...
✅ Saved 0 papers, embedded 20 papers
```

### **Analysis:**
1. **Papers ARE being saved**: "updated 1040 existing papers"
2. **Embeddings ARE being generated**: "embedded 20 papers"
3. **Search returns 0**: hybrid_search finds nothing

### **Possible Causes:**

#### **Cause A: Embedding Search Threshold Too High**
```python
# Vector similarity search might require exact matches
# If similarity threshold is 0.9, "machine learning" won't match "deep learning"
```

#### **Cause B: Category Filter Too Strict**
```python
# Search filters by category='ai_cs'
# But papers might be saved with different category format
```

#### **Cause C: Embeddings Not Committed to Database**
```python
# Embeddings generated but not flushed/committed
db.commit()  # Missing?
```

#### **Cause D: Query Embedding Not Generated**
```python
# Search query "machine learning" needs to be embedded first
# Then compared with paper embeddings
# If query embedding fails, no results
```

---

## 🔍 **Investigation Needed**

### **Check #1: Verify Papers in Database**
```sql
SELECT COUNT(*) FROM papers WHERE category = 'ai_cs';
SELECT COUNT(*) FROM papers WHERE embedding IS NOT NULL;
```

### **Check #2: Check hybrid_search Implementation**
```python
# Need to see vector_service.hybrid_search() code
# Check:
# 1. Is it generating query embedding?
# 2. What's the similarity threshold?
# 3. Is category filter working?
```

### **Check #3: Test Direct Database Query**
```python
# Bypass hybrid_search, query papers directly
papers = db.query(Paper).filter(Paper.category == 'ai_cs').limit(20).all()
print(f"Direct query found: {len(papers)} papers")
```

---

## 🎯 **Recommended Fixes**

### **Fix #1: Disable Auto-Reload for Testing**
```bash
# Instead of:
uvicorn app.main:app --reload

# Use:
uvicorn app.main:app  # No --reload
```
This will keep in-memory cache between requests.

### **Fix #2: Lower Similarity Threshold**
```python
# In hybrid_search, reduce threshold
similarity_threshold = 0.5  # Instead of 0.8 or 0.9
```

### **Fix #3: Add Debug Logging**
```python
# In hybrid_search
print(f"Query embedding shape: {query_embedding.shape}")
print(f"Papers with embeddings: {db.query(Paper).filter(Paper.embedding != None).count()}")
print(f"Similarity scores: {similarities[:5]}")
```

### **Fix #4: Implement Redis Cache**
```python
# Replace in-memory cache with Redis
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)
```

---

## 📝 **Next Steps**

1. Check `vector_service.py` hybrid_search implementation
2. Add debug logging to see what's happening
3. Test direct database query
4. Lower similarity threshold if needed
5. Implement proper Redis caching

**Want me to investigate the vector service code?**
