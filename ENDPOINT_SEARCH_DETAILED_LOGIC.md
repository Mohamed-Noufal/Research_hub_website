# Search Endpoint Detailed Logic
## Intelligent Hybrid Search Strategy

**Version:** 1.0  
**Date:** 2025-11-22  
**Status:** Design Document

---

## 🎯 **Core Strategy**

**Goal:** Fast, comprehensive results that grow smarter over time

**Approach:** Parallel local + external search → Merge → Background embedding generation

---

## 📊 **Search Flow Diagram**

```
User searches "machine learning" in category "AI & CS"
         ↓
    ┌────────────────────────────────────┐
    │   PARALLEL EXECUTION (Fast!)       │
    ├────────────────┬───────────────────┤
    │                │                   │
    ▼                ▼                   ▼
[Local DB]    [Category-Specific     [Backup Sources]
threshold=0.3   External Sources]    (If primary fails)
    │                │                   │
    │         ┌──────┴──────┐            │
    │         ▼              ▼            │
    │    AI & CS:        Medicine:        │
    │    - arXiv         - PubMed         │
    │    - Semantic      - Europe PMC     │
    │      Scholar       - Crossref       │
    │                                     │
    │    Agriculture:    Humanities:      │
    │    - OpenAlex      - ERIC           │
    │    - CORE          - OpenAlex       │
    │                                     │
    │    Economics:                       │
    │    - OpenAlex                       │
    │    - Crossref                       │
    │                                     │
    ▼                ▼                   ▼
 10-20 papers    20 papers          20 papers
    │                │                   │
    └────────────────┴───────────────────┘
                     ↓
            ┌────────────────┐
            │ MERGE RESULTS  │
            │ - Deduplicate  │
            │ - Rank by score│
            └────────────────┘
                     ↓
            ┌────────────────┐
            │ RETURN TO USER │
            │   (10-15s)     │
            └────────────────┘
                     ↓
            ┌────────────────┐
            │   BACKGROUND   │
            │ - Save papers  │
            │ - Generate     │
            │   embeddings   │
            │ (Don't wait!)  │
            └────────────────┘
```

---

## 🎯 **Category-Specific Source Routing**

### **Category: AI & Computer Science (`ai_cs`)**
```python
SOURCES = {
    'primary': 'arxiv',           # Best for CS/AI papers
    'backup_1': 'semantic_scholar', # Comprehensive coverage
    'backup_2': 'openalex'         # Final fallback
}
```

### **Category: Medicine & Biology (`medicine_biology`)**
```python
SOURCES = {
    'primary': 'pubmed',           # Medical literature database
    'backup_1': 'europe_pmc',      # European medical papers
    'backup_2': 'crossref'         # DOI-based fallback
}
```

### **Category: Agriculture & Animal Science (`agriculture_animal`)**
```python
SOURCES = {
    'primary': 'openalex',         # Broad coverage
    'backup_1': 'core',            # Open access repository
    'backup_2': 'crossref'         # DOI-based fallback
}
```

### **Category: Humanities & Social Sciences (`humanities_social`)**
```python
SOURCES = {
    'primary': 'eric',             # Education resources
    'backup_1': 'openalex',        # Broad coverage
    'backup_2': 'semantic_scholar' # Academic papers
}
```

### **Category: Economics & Business (`economics_business`)**
```python
SOURCES = {
    'primary': 'openalex',         # Economics papers
    'backup_1': 'crossref',        # DOI-based search
    'backup_2': 'semantic_scholar' # Academic coverage
}
```

---

## 🔄 **Detailed Search Logic**

### **Phase 1: Parallel Search (5-10 seconds)**

#### **1.1 Local Database Search**
```python
async def search_local_database(query: str, category: str):
    """
    Search embedded local data
    
    Threshold: 0.4 (good recall)
    Limit: 20 papers
    Fast: ~1-2 seconds
    """
    results = await hybrid_search(
        query=query,
        category=category,
        threshold=0.4,
        limit=20
    )
    return results
```

**Characteristics:**
- ✅ Very fast (1-2s)
- ✅ Semantically relevant
- ✅ Already embedded
- ⚠️ Limited to existing data (1041 papers currently)

---

#### **1.2 External API Search (Parallel)**

**Note:** Each external source searches for **maximum results** to build comprehensive database

**Primary Source: arXiv**
```python
async def search_arxiv(query: str, limit: int = 100):
    """
    Primary external source
    
    Reliability: 99%
    Speed: 3-5 seconds
    Coverage: 2M+ papers
    Max results: 100 per query (arXiv API limit)
    """
    try:
        results = await arxiv_service.search(query, limit=100)  # Max limit
        return results
    except Exception as e:
        print(f"❌ arXiv failed: {e}")
        return None
```

**Backup 1: Semantic Scholar**
```python
async def search_semantic_scholar(query: str, limit: int = 100):
    """
    Backup source if arXiv fails
    
    Reliability: 95%
    Speed: 5-8 seconds
    Coverage: 200M+ papers
    Max results: 100 per query (API limit)
    """
    try:
        results = await semantic_scholar_service.search(query, limit=100)  # Max limit
        return results
    except Exception as e:
        print(f"❌ Semantic Scholar failed: {e}")
        return None
```

**Backup 2: OpenAlex**
```python
async def search_openalex(query: str, limit: int = 200):
    """
    Final fallback source
    
    Reliability: 90%
    Speed: 8-10 seconds
    Coverage: 250M+ papers
    Max results: 200 per query (API limit)
    """
    try:
        results = await openalex_service.search(query, limit=200)  # Max limit
        return results
    except Exception as e:
        print(f"❌ OpenAlex failed: {e}")
        return None
```

**Other Sources:**
- **PubMed:** Max 100 results per query
- **Europe PMC:** Max 100 results per query
- **Crossref:** Max 100 results per query
- **ERIC:** Max 100 results per query
- **CORE:** Max 100 results per query

---

#### **1.3 Category-Based External Source Selection**

```python
# Category to source mapping
CATEGORY_SOURCES = {
    'ai_cs': {
        'primary': 'arxiv',
        'backup_1': 'semantic_scholar',
        'backup_2': 'openalex'
    },
    'medicine_biology': {
        'primary': 'pubmed',
        'backup_1': 'europe_pmc',
        'backup_2': 'crossref'
    },
    'agriculture_animal': {
        'primary': 'openalex',
        'backup_1': 'core',
        'backup_2': 'crossref'
    },
    'humanities_social': {
        'primary': 'eric',
        'backup_1': 'openalex',
        'backup_2': 'semantic_scholar'
    },
    'economics_business': {
        'primary': 'openalex',
        'backup_1': 'crossref',
        'backup_2': 'semantic_scholar'
    }
}

async def get_sources_for_category(category: str) -> dict:
    """
    Get appropriate sources for the given category
    
    Returns:
        {
            'primary': 'arxiv',
            'backup_1': 'semantic_scholar',
            'backup_2': 'openalex'
        }
    """
    return CATEGORY_SOURCES.get(category, {
        'primary': 'arxiv',  # Default to arXiv
        'backup_1': 'semantic_scholar',
        'backup_2': 'openalex'
    })
```

---

#### **1.4 Cascading External Search with Category Routing**

```python
async def search_external_with_fallback(query: str, category: str):
    """
    Search external sources based on category
    Try primary → backup_1 → backup_2
    """
    
    # Get sources for this category
    sources = await get_sources_for_category(category)
    
    # Try primary source
    primary_source = sources['primary']
    print(f"🔍 Category: {category} → PRIMARY source: {primary_source}")
    results = await search_source(primary_source, query, limit=20)
    if results and len(results) > 0:
        print(f"✅ {primary_source}: {len(results)} papers found")
        return {'papers': results, 'source': primary_source}
    
    # Try backup 1
    backup_1 = sources['backup_1']
    print(f"🔍 PRIMARY failed → BACKUP 1: {backup_1}")
    results = await search_source(backup_1, query, limit=20)
    if results and len(results) > 0:
        print(f"✅ {backup_1}: {len(results)} papers found")
        return {'papers': results, 'source': backup_1}
    
    # Try backup 2
    backup_2 = sources['backup_2']
    print(f"🔍 BACKUP 1 failed → BACKUP 2: {backup_2}")
    results = await search_source(backup_2, query, limit=20)
    if results and len(results) > 0:
        print(f"✅ {backup_2}: {len(results)} papers found")
        return {'papers': results, 'source': backup_2}
    
    # All sources failed
    print(f"❌ All sources failed for category: {category}")
    return {'papers': [], 'source': 'none'}


async def search_source(source_name: str, query: str, limit: int = None):
    """
    Generic source search wrapper
    Routes to appropriate service based on source name
    Uses maximum limit for each API to get comprehensive results
    """
    
    # Define max limits for each source
    MAX_LIMITS = {
        'arxiv': 100,
        'semantic_scholar': 100,
        'openalex': 200,
        'pubmed': 100,
        'europe_pmc': 100,
        'crossref': 100,
        'eric': 100,
        'core': 100
    }
    
    # Use max limit for the source
    max_limit = MAX_LIMITS.get(source_name, 100)
    
    try:
        if source_name == 'arxiv':
            return await arxiv_service.search(query, max_limit)
        elif source_name == 'pubmed':
            return await pubmed_service.search(query, max_limit)
        elif source_name == 'semantic_scholar':
            return await semantic_scholar_service.search(query, max_limit)
        elif source_name == 'openalex':
            return await openalex_service.search(query, max_limit)
        elif source_name == 'europe_pmc':
            return await europe_pmc_service.search(query, max_limit)
        elif source_name == 'crossref':
            return await crossref_service.search(query, max_limit)
        elif source_name == 'eric':
            return await eric_service.search(query, max_limit)
        elif source_name == 'core':
            return await core_service.search(query, max_limit)
        else:
            print(f"⚠️ Unknown source: {source_name}")
            return None
    except Exception as e:
        print(f"❌ {source_name} error: {e}")
        return None
```

**Example Flow:**

**Search "deep learning" in AI & CS:**
```
1. Try arXiv (primary for AI) → Success! ✅
2. Return 100 papers from arXiv (max limit)
```

**Search "cancer treatment" in Medicine:**
```
1. Try PubMed (primary for medicine) → Success! ✅
2. Return 100 papers from PubMed (max limit)
```

**Search "crop yield" in Agriculture:**
```
1. Try OpenAlex (primary for agriculture) → Failed ❌
2. Try CORE (backup 1) → Success! ✅
3. Return 100 papers from CORE (max limit)
```

**Benefits of Maximum Results:**
- ✅ More comprehensive data collection
- ✅ Faster database growth (100-200 papers per search vs 20)
- ✅ Better coverage of research topics
- ✅ Users get more diverse results
- ✅ Database becomes useful faster

---

### **Phase 2: Merge & Deduplicate (1-2 seconds)**

```python
async def merge_and_deduplicate(local_results, external_results):
    """
    Combine local and external results
    Remove duplicates by DOI, arXiv ID, or title similarity
    """
    
    all_papers = []
    seen_identifiers = set()
    
    # Add local results first (higher priority)
    for paper in local_results:
        identifier = paper.get('doi') or paper.get('arxiv_id') or paper.get('title')
        if identifier not in seen_identifiers:
            paper['source_type'] = 'local'
            all_papers.append(paper)
            seen_identifiers.add(identifier)
    
    # Add external results (new papers)
    for paper in external_results:
        identifier = paper.get('doi') or paper.get('arxiv_id') or paper.get('title')
        if identifier not in seen_identifiers:
            paper['source_type'] = 'external'
            all_papers.append(paper)
            seen_identifiers.add(identifier)
    
    print(f"📊 Merged: {len(local_results)} local + {len(external_results)} external = {len(all_papers)} total")
    
    return all_papers
```

**Deduplication Strategy:**
1. Check DOI (most reliable)
2. Check arXiv ID
3. Check title similarity (fuzzy match)
4. Keep first occurrence

---

### **Phase 3: Return Results (Immediate)**

```python
async def unified_search(query: str, category: str):
    """
    Main search endpoint
    Returns results in 10-15 seconds
    """
    
    start_time = time.time()
    
    # PARALLEL: Search local + external simultaneously
    local_task = asyncio.create_task(search_local_database(query, category))
    external_task = asyncio.create_task(search_external_with_fallback(query, category))
    
    # Wait for both to complete
    local_results, external_results = await asyncio.gather(local_task, external_task)
    
    # Merge and deduplicate
    merged_papers = await merge_and_deduplicate(
        local_results.get('papers', []),
        external_results.get('papers', [])
    )
    
    # Prepare response
    response = {
        'papers': merged_papers,
        'total': len(merged_papers),
        'sources': {
            'local': len(local_results.get('papers', [])),
            'external': len(external_results.get('papers', [])),
            'external_source': external_results.get('source')
        },
        'search_time': time.time() - start_time,
        'cached': False
    }
    
    # BACKGROUND: Save and embed new papers (don't wait!)
    new_papers = [p for p in merged_papers if p.get('source_type') == 'external']
    if new_papers:
        background_tasks.add_task(
            save_and_embed_papers,
            papers=new_papers,
            category=category
        )
    
    return response
```

**Response Time:**
- Local search: 1-2s
- External search: 3-8s (parallel)
- Merge: 1s
- **Total: 10-15 seconds** ⚡

---

### **Phase 4: Background Processing (Async)**

```python
async def save_and_embed_papers(papers: List[Dict], category: str):
    """
    Background task - runs AFTER response is sent
    User doesn't wait for this!
    """
    
    print(f"🔄 BACKGROUND: Processing {len(papers)} new papers")
    
    # 1. Save papers to database (fast)
    saved_papers = await save_papers_to_db(papers, category)
    print(f"💾 Saved {len(saved_papers)} papers")
    
    # 2. Generate embeddings (slow, but user doesn't wait!)
    embeddings_generated = await generate_embeddings_batch(saved_papers)
    print(f"🧠 Generated {embeddings_generated} embeddings")
    
    print(f"✅ BACKGROUND: Complete! Database now has more data for next search")
```

**What happens in background:**
1. Save papers to database (~2s)
2. Generate embeddings (~100s)
3. Update database with embeddings

**User experience:**
- Gets results in 10-15s
- Doesn't wait for embeddings
- Next search will have more local data!

---

## 🚀 **Future Optimization: Smart Local-First**

**When database grows to 100k+ papers:**

```python
async def smart_search(query: str, category: str):
    """
    Future optimization: Only search external if needed
    """
    
    # 1. Search local database
    local_results = await search_local_database(query, category)
    
    # 2. Check if we have enough high-quality results
    high_quality_results = [
        p for p in local_results 
        if p.get('hybrid_score', 0) >= 0.85  # 85% threshold
    ]
    
    # 3. Decision: Do we need external search?
    if len(high_quality_results) >= 1000:
        # We have plenty of excellent local results!
        print("✅ Sufficient local data, skipping external search")
        return {
            'papers': local_results[:50],  # Return top 50
            'source': 'local_only',
            'search_time': '~2 seconds'
        }
    else:
        # Need more/better results, search external
        print("🔍 Insufficient local data, searching external APIs")
        return await unified_search(query, category)
```

**Threshold Logic:**
- **< 1000 papers with 85% similarity:** Search external (get fresh data)
- **≥ 1000 papers with 85% similarity:** Local only (fast!)

---

## 📈 **Database Growth Strategy**

### **Week 1: Bootstrap Phase**
- Database: 1,041 papers
- Every search adds 10-20 new papers
- 100 searches/day = 1,000-2,000 new papers/day

### **Month 1: Growth Phase**
- Database: 50,000 papers
- 50% of searches find local results
- 50% still need external search

### **Month 3: Mature Phase**
- Database: 500,000 papers
- 80% of searches use local only
- 20% search external for rare queries

### **Month 6: Optimized Phase**
- Database: 2,000,000 papers
- 95% local searches (fast!)
- 5% external for cutting-edge research

---

## 🎯 **Success Metrics**

### **Performance**
- ✅ Search time: < 15 seconds (currently ~116s)
- ✅ Local hit rate: Grows from 0% → 95%
- ✅ User satisfaction: Fresh + fast results

### **Data Quality**
- ✅ Deduplication rate: > 95%
- ✅ Relevance score: > 0.3 average
- ✅ Coverage: All major research areas

### **Scalability**
- ✅ Database growth: 1k → 2M papers in 6 months
- ✅ Search speed: Improves as database grows
- ✅ Cost: Decreases (fewer external API calls)

---

## 🔧 **Implementation Checklist**

### **Phase 1: Immediate (Today)**
- [ ] Implement parallel local + external search
- [ ] Add merge and deduplication logic
- [ ] Move embedding generation to background task
- [ ] Test search time (should be ~10-15s)

### **Phase 2: Short-term (This Week)**
- [ ] Implement cascading external search (arXiv → Semantic Scholar → OpenAlex)
- [ ] Add error handling for API failures
- [ ] Monitor database growth rate
- [ ] Add search analytics

### **Phase 3: Long-term (This Month)**
- [ ] Implement smart local-first logic
- [ ] Add 85% threshold check for 1000+ papers
- [ ] Optimize embedding generation (GPU?)
- [ ] Add caching for common queries

---

## 🎉 **Expected Results**

**Before:**
- Search time: 116 seconds
- Results: Same 20 papers every time
- Database: Static (1041 papers)

**After:**
- Search time: 10-15 seconds (11x faster!)
- Results: Mix of local + fresh external
- Database: Grows organically (1k → 2M papers)

**User Experience:**
- ✅ Fast results
- ✅ Fresh content
- ✅ Growing intelligence
- ✅ Never feels limited

---

## 📝 **Notes**

1. **Embedding generation is async** - User never waits for it
2. **External search has fallbacks** - Always get results
3. **Database grows automatically** - Every search adds value
4. **Smart optimization later** - When database is large enough

**This strategy ensures users get fast, comprehensive results while building a powerful local database for the future!**
