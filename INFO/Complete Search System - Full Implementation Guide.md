PART 1: UX DESIGN - Two Search Options
Option A: Two Separate Search Bars
┌──────────────────────────────────────────────────────┐
│  🔍 Quick Search                    [Category ▼]     │
│  ┌────────────────────────────────────────────────┐  │
│  │ machine learning                    [Search]   │  │
│  └────────────────────────────────────────────────┘  │
│  💡 Fast keyword search across top sources          │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  🤖 AI-Powered Search               [Category ▼]     │
│  ┌────────────────────────────────────────────────┐  │
│  │ How do neural networks learn from data? [🔍]  │  │
│  └────────────────────────────────────────────────┘  │
│  ✨ Ask in natural language, AI finds best papers   │
└──────────────────────────────────────────────────────┘
Pros:

Clear separation for users
Power users can choose mode
Can optimize each separately

Cons:

Two UI elements (slight clutter)
User needs to decide which to use


Option B: One Smart Search Bar (Auto-Detect)
┌──────────────────────────────────────────────────────┐
│  🔍 Search papers...                [Category ▼]     │
│  ┌────────────────────────────────────────────────┐  │
│  │ How do neural networks learn?      [Search 🤖] │  │
│  └────────────────────────────────────────────────┘  │
│  💡 AI detects if you need smart search or keyword  │
│                                                      │
│  [⚡ Quick Mode]  [🤖 AI Mode]  [Auto ✓]            │
└──────────────────────────────────────────────────────┘
Auto-detection logic:
pythondef detect_search_mode(query: str) -> str:
    """Auto-detect if user needs AI search or keyword search"""
    
    # Triggers for AI mode
    question_words = ["how", "what", "why", "when", "where", "who"]
    long_query = len(query.split()) > 6
    natural_language = any(word in query.lower() for word in question_words)
    
    if natural_language or long_query:
        return "ai_mode"  # Use AI agent
    else:
        return "quick_mode"  # Use keyword search
Pros:

One clean search bar
Auto-detects user intent
Less cognitive load

Cons:

Might not always detect correctly
Less explicit control


🏆 RECOMMENDED: Hybrid Approach
┌──────────────────────────────────────────────────────┐
│  🔍 Search research papers...       [Category ▼]     │
│  ┌────────────────────────────────────────────────┐  │
│  │ machine learning                    [Search]   │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  🤖 [Use AI Search]  💡 Better for natural questions│
└──────────────────────────────────────────────────────┘
When user types question, show suggestion:
┌──────────────────────────────────────────────────────┐
│  🔍 How do neural networks learn from data?          │
│  ┌────────────────────────────────────────────────┐  │
│  │ How do neural networks learn from data?        │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ✨ Detected question - Try AI Search for better    │
│     results? [Yes, use AI] [No, keyword search]     │
└──────────────────────────────────────────────────────┘

🏗️ PART 2: COMPLETE BACKEND ARCHITECTURE
System Overview:
Frontend Request
      ↓
Smart Router (decides mode)
      ↓
┌─────────────┬──────────────┐
│             │              │
Quick Search  AI Search      
│             │              
↓             ↓              
Category      AI Agent
Selector      (optimize)
│             │
↓             ↓
Cache Check   Cache Check
│             │
↓             ↓
Primary       Primary
Source        Source
│             │
↓             ↓
Backup        Backup
(if needed)   (if needed)
│             │
↓             ↓
Deduplicate   Deduplicate
│             │
↓             ↓
Semantic      Semantic
Rerank        Rerank
│             │
└─────────────┴──────────────┘
      ↓
Return Results

💻 IMPLEMENTATION
1. Configuration File - Sources & Categories
python# app/config/search_config.py

class SearchConfig:
    """Central configuration for all search sources and categories"""
    
    # Define all available sources
    SOURCES = {
        "arxiv": {
            "name": "arXiv",
            "description": "Computer Science, Physics, Math preprints",
            "api_class": "ArxivService",
            "rate_limit": 100,  # calls per minute
            "reliability": 0.95,
            "speed": "fast",
            "specialties": ["cs", "physics", "math"]
        },
        "semantic_scholar": {
            "name": "Semantic Scholar",
            "description": "AI-powered all-discipline search",
            "api_class": "SemanticScholarService",
            "rate_limit": 100,
            "reliability": 0.90,
            "speed": "medium",
            "specialties": ["all"]
        },
        "openalex": {
            "name": "OpenAlex",
            "description": "Global research database",
            "api_class": "OpenAlexService",
            "rate_limit": 500,
            "reliability": 0.85,
            "speed": "fast",
            "specialties": ["all"]
        },
        "pubmed": {
            "name": "PubMed",
            "description": "Biomedical literature",
            "api_class": "PubMedService",
            "rate_limit": 60,
            "reliability": 0.98,
            "speed": "medium",
            "specialties": ["medicine", "biology"]
        },
        "europe_pmc": {
            "name": "Europe PMC",
            "description": "European biomedical research",
            "api_class": "EuropePMCService",
            "rate_limit": 100,
            "reliability": 0.85,
            "speed": "medium",
            "specialties": ["medicine", "biology"]
        },
        "crossref": {
            "name": "Crossref",
            "description": "DOI resolution and metadata",
            "api_class": "CrossrefService",
            "rate_limit": 500,
            "reliability": 0.90,
            "speed": "fast",
            "specialties": ["all"]
        },
        "core": {
            "name": "CORE",
            "description": "Open access research",
            "api_class": "CoreService",
            "rate_limit": 50,
            "reliability": 0.70,  # Sometimes unreliable
            "speed": "slow",
            "specialties": ["all"]
        }
    }
    
    # Define categories with source hierarchy
    CATEGORIES = {
        "ai_cs": {
            "name": "AI & Computer Science",
            "description": "Machine learning, AI, computer vision, NLP",
            "sources": {
                "primary": "arxiv",         # 80% success
                "backup": "semantic_scholar", # 15% success
                "fallback": "openalex"       # 5% success
            },
            "keywords": ["machine learning", "deep learning", "AI", "neural network", 
                        "computer vision", "NLP", "algorithm"]
        },
        "medicine_biology": {
            "name": "Medicine & Biology",
            "description": "Clinical research, biomedical, healthcare",
            "sources": {
                "primary": "pubmed",
                "backup": "europe_pmc",
                "fallback": "crossref"
            },
            "keywords": ["cancer", "disease", "clinical", "medical", "patient",
                        "treatment", "diagnosis", "therapy", "drug"]
        },
        "engineering_physics": {
            "name": "Engineering & Physics",
            "description": "Applied sciences, engineering, physics",
            "sources": {
                "primary": "arxiv",
                "backup": "openalex",
                "fallback": "crossref"
            },
            "keywords": ["engineering", "physics", "quantum", "materials",
                        "mechanics", "system", "design"]
        },
        "agriculture_animal": {
            "name": "Agriculture & Animal Science",
            "description": "Farming, animal science, food security",
            "sources": {
                "primary": "openalex",
                "backup": "core",
                "fallback": "crossref"
            },
            "keywords": ["agriculture", "farming", "livestock", "crop",
                        "animal", "soil", "food"]
        },
        "humanities_social": {
            "name": "Humanities & Social Sciences",
            "description": "Psychology, sociology, education, humanities",
            "sources": {
                "primary": "core",
                "backup": "openalex",
                "fallback": "crossref"
            },
            "keywords": ["psychology", "sociology", "education", "social",
                        "culture", "history", "philosophy"]
        },
        "economics_business": {
            "name": "Economics & Business",
            "description": "Economics, finance, business management",
            "sources": {
                "primary": "openalex",
                "backup": "core",
                "fallback": "crossref"
            },
            "keywords": ["economics", "business", "finance", "market",
                        "trade", "management", "investment"]
        },
        "general": {
            "name": "General (All Fields)",
            "description": "Cross-disciplinary and general research",
            "sources": {
                "primary": "semantic_scholar",
                "backup": "openalex",
                "fallback": "crossref"
            },
            "keywords": []
        }
    }
    
    @classmethod
    def auto_detect_category(cls, query: str) -> str:
        """Auto-detect category from query keywords"""
        query_lower = query.lower()
        
        # Score each category
        scores = {}
        for category_id, category_info in cls.CATEGORIES.items():
            score = sum(1 for keyword in category_info['keywords'] 
                       if keyword in query_lower)
            scores[category_id] = score
        
        # Return category with highest score
        best_category = max(scores, key=scores.get)
        
        # If no keywords match, return general
        if scores[best_category] == 0:
            return "general"
        
        return best_category
    
    @classmethod
    def get_source_hierarchy(cls, category: str) -> list:
        """Get source search order for a category"""
        category_info = cls.CATEGORIES.get(category, cls.CATEGORIES["general"])
        sources = category_info['sources']
        
        return [
            sources['primary'],
            sources['backup'],
            sources['fallback']
        ]

2. Unified Search Service (Handles Everything)
python# app/services/unified_search_service.py

class UnifiedSearchService:
    """
    One service that handles:
    - Quick search (keyword)
    - AI search (agent-powered)
    - Category detection
    - Source cascading
    - Caching
    - Deduplication
    - Semantic reranking
    """
    
    def __init__(self):
        self.config = SearchConfig()
        self.cache = EnhancedCacheService(settings.REDIS_URL)
        self.query_agent = QueryOptimizerAgent(settings.GROQ_API_KEY)
        
        # Initialize all sources
        self.sources = {}
        for source_id, source_config in self.config.SOURCES.items():
            try:
                source_class = globals()[source_config['api_class']]
                self.sources[source_id] = source_class()
            except Exception as e:
                print(f"Failed to initialize {source_id}: {e}")
        
        self.embedding_model = SentenceTransformer('nomic-embed-text-v1.5')
    
    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        mode: str = "auto",  # "auto", "quick", "ai"
        limit: int = 20,
        min_results: int = 10
    ) -> dict:
        """
        Universal search endpoint
        
        Args:
            query: User's search query
            category: Force specific category (or auto-detect)
            mode: Search mode (auto/quick/ai)
            limit: Max results to return
            min_results: Min results before trying backup
        """
        
        start_time = time.time()
        
        # STEP 1: Detect mode if auto
        if mode == "auto":
            mode = self._detect_mode(query)
        
        print(f"\n{'='*60}")
        print(f"🔍 SEARCH REQUEST")
        print(f"{'='*60}")
        print(f"Query: {query}")
        print(f"Mode: {mode}")
        print(f"Category: {category or 'auto-detect'}")
        
        # STEP 2: Check cache first (semantic matching)
        cache_key = f"{query}:{category or 'auto'}:{mode}"
        cached_result = await self.cache.get_semantic_cache(
            query=query,
            category=category or "auto",
            similarity_threshold=0.85
        )
        
        if cached_result:
            print(f"✅ CACHE HIT (saved {time.time() - start_time:.2f}s)")
            cached_result['metadata']['cached'] = True
            cached_result['metadata']['search_time'] = time.time() - start_time
            return cached_result
        
        print(f"❌ Cache miss, performing search...")
        
        # STEP 3: Route to appropriate search method
        if mode == "ai":
            result = await self._ai_search(query, category, limit, min_results)
        else:
            result = await self._quick_search(query, category, limit, min_results)
        
        # STEP 4: Cache the result
        await self.cache.cache_results(
            query=query,
            category=category or result['metadata']['category'],
            results=result
        )
        
        # STEP 5: Add timing
        result['metadata']['search_time'] = time.time() - start_time
        result['metadata']['cached'] = False
        
        print(f"\n{'='*60}")
        print(f"✅ SEARCH COMPLETE")
        print(f"{'='*60}")
        print(f"Mode: {mode}")
        print(f"Results: {len(result['papers'])}")
        print(f"API calls: {result['metadata']['api_calls_made']}")
        print(f"Time: {result['metadata']['search_time']:.2f}s")
        print(f"{'='*60}\n")
        
        return result
    
    def _detect_mode(self, query: str) -> str:
        """Auto-detect if query needs AI or quick search"""
        question_words = ["how", "what", "why", "when", "where", "who", "which"]
        
        query_lower = query.lower()
        is_question = any(query_lower.startswith(word) for word in question_words)
        is_long = len(query.split()) > 6
        
        if is_question or is_long:
            return "ai"
        return "quick"
    
    async def _quick_search(
        self,
        query: str,
        category: Optional[str],
        limit: int,
        min_results: int
    ) -> dict:
        """Quick keyword search with cascading fallback"""
        
        # Auto-detect category if not provided
        if not category:
            category = self.config.auto_detect_category(query)
        
        print(f"\n🚀 QUICK SEARCH MODE")
        print(f"Category: {category}")
        
        # Get source hierarchy
        source_order = self.config.get_source_hierarchy(category)
        
        # Cascading search
        return await self._cascading_search(
            query=query,
            source_order=source_order,
            category=category,
            limit=limit,
            min_results=min_results,
            mode="quick"
        )
    
    async def _ai_search(
        self,
        query: str,
        category: Optional[str],
        limit: int,
        min_results: int
    ) -> dict:
        """AI-powered search with query optimization"""
        
        print(f"\n🤖 AI SEARCH MODE")
        
        # STEP 1: AI agent optimizes query
        optimization = await self.query_agent.optimize_query(query)
        
        print(f"\n✨ AI OPTIMIZATION:")
        print(f"Original: {query}")
        print(f"Optimized: {optimization['optimized_query']}")
        print(f"Category: {optimization['category']}")
        print(f"Intent: {optimization['intent']}")
        print(f"Confidence: {optimization['confidence']:.2f}")
        
        # Use AI-detected category unless user specified
        if not category:
            category = optimization['category']
        
        # Get source hierarchy
        source_order = self.config.get_source_hierarchy(category)
        
        # Cascading search with optimized query
        result = await self._cascading_search(
            query=optimization['optimized_query'],
            source_order=source_order,
            category=category,
            limit=limit,
            min_results=min_results,
            mode="ai"
        )
        
        # Add AI metadata
        result['metadata']['ai_optimization'] = optimization
        result['metadata']['original_query'] = query
        
        return result
    
    async def _cascading_search(
        self,
        query: str,
        source_order: list,
        category: str,
        limit: int,
        min_results: int,
        mode: str
    ) -> dict:
        """Core cascading search logic with fallback"""
        
        all_results = []
        sources_tried = []
        api_calls = 0
        
        for i, source_id in enumerate(source_order):
            source = self.sources.get(source_id)
            
            if not source:
                print(f"⚠️  Source {source_id} not available")
                continue
            
            try:
                print(f"\n🔍 Attempt {i+1}: Searching {source_id}...")
                
                # Search this source
                results = await source.search(query, limit=limit * 2)
                api_calls += 1
                sources_tried.append(source_id)
                
                print(f"✅ {source_id}: {len(results)} papers")
                
                all_results.extend(results)
                
                # Deduplicate to check progress
                deduplicated = deduplicate_papers(all_results)
                
                print(f"📊 Total unique papers so far: {len(deduplicated)}")
                
                # Check if we have enough
                if len(deduplicated) >= min_results:
                    print(f"🎉 Sufficient results! Stopping search.")
                    break
                else:
                    print(f"⚠️  Need more results, trying backup...")
                    
            except Exception as e:
                print(f"❌ {source_id} failed: {e}")
                continue
        
        # Final deduplication
        print(f"\n📊 DEDUPLICATION:")
        print(f"Before: {len(all_results)} papers")
        
        deduplicated = deduplicate_papers(all_results)
        
        print(f"After: {len(deduplicated)} papers")
        
        # Semantic reranking
        print(f"\n🧠 SEMANTIC RERANKING...")
        
        reranked = await self._semantic_rerank(
            query=query,
            papers=deduplicated,
            top_k=limit
        )
        
        print(f"✅ Top {len(reranked)} papers selected")
        
        # Prepare response
        return {
            "papers": reranked,
            "total": len(reranked),
            "metadata": {
                "query": query,
                "category": category,
                "mode": mode,
                "sources_tried": sources_tried,
                "api_calls_made": api_calls,
                "papers_before_dedup": len(all_results),
                "papers_after_dedup": len(deduplicated),
                "source_hierarchy": source_order
            }
        }
    
    async def _semantic_rerank(
        self,
        query: str,
        papers: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """Semantic reranking using embeddings"""
        
        if not papers:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Generate paper embeddings
        paper_texts = [
            f"{p.get('title', '')} {p.get('abstract', '')[:500]}"
            for p in papers
        ]
        
        paper_embeddings = self.embedding_model.encode(paper_texts)
        
        # Calculate similarities
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            paper_embeddings
        )[0]
        
        # Add scores and rank
        for i, paper in enumerate(papers):
            paper['semantic_score'] = float(similarities[i])
            
            # Hybrid score
            citation_score = min(paper.get('citation_count', 0) / 10000, 1.0)
            paper['hybrid_score'] = 0.7 * paper['semantic_score'] + 0.3 * citation_score
        
        # Sort by hybrid score
        sorted_papers = sorted(
            papers,
            key=lambda x: x.get('hybrid_score', 0),
            reverse=True
        )
        
        return sorted_papers[:top_k]

3. API Endpoints
python# app/api/v1/papers.py

@router.get("/categories")
async def get_categories():
    """Get all available categories"""
    return {
        "categories": [
            {
                "id": cat_id,
                "name": cat_info['name'],
                "description": cat_info['description'],
                "sources": cat_info['sources']
            }
            for cat_id, cat_info in SearchConfig.CATEGORIES.items()
        ]
    }


@router.get("/search")
async def unified_search(
    query: str = Query(..., min_length=2, max_length=500),
    category: Optional[str] = Query(None),
    mode: str = Query("auto", regex="^(auto|quick|ai)$"),
    limit: int = Query(20, ge=1, le=100),
    min_results: int = Query(10, ge=5, le=50)
):
    """
    🔍 Universal Search Endpoint
    
    **Supports two modes:**
    
    1. **Quick Search** (keyword-based)
       - Fast keyword search
       - Example: "machine learning"
    
    2. **AI Search** (agent-powered)
       - Natural language understanding
       - Example: "How do neural networks learn?"
    
    3. **Auto** (detects which mode to use)
       - Automatic detection based on query
    
    **How it works:**
    - Checks cache first (semantic matching)
    - Routes to primary source for category
    - Falls back to backup if needed
    - Deduplicates and reranks results
    - Caches for future searches
    
    **Parameters:**
    - query: Search terms or natural language question
    - category: Force specific category (or auto-detect)
    - mode: "auto" (default), "quick", or "ai"
    - limit: Max results (1-100, default 20)
    - min_results: Min results before backup (default 10)
    
    **Example Requests:**
# Quick keyword search
GET /search?query=machine learning&mode=quick

# AI-powered natural language
GET /search?query=how do transformers work&mode=ai

# Auto-detect mode
GET /search?query=deep learning

# Force category
GET /search?query=cancer treatment&category=medicine_biology
    """
    
    result = await unified_search_service.search(
        query=query,
        category=category,
        mode=mode,
        limit=limit,
        min_results=min_results
    )
    
    return result


@router.get("/search/suggest")
async def search_suggestions(
    query: str = Query(..., min_length=2)
):
    """
    💡 Get search suggestions
    
    Returns:
    - Suggested mode (quick/ai)
    - Detected category
    - Alternative queries
    """
    
    mode = unified_search_service._detect_mode(query)
    category = SearchConfig.auto_detect_category(query)
    
    return {
        "query": query,
        "suggested_mode": mode,
        "detected_category": category,
        "category_info": SearchConfig.CATEGORIES[category],
        "tip": "Try AI search for better results" if mode == "ai" else "Quick search is perfect for this"
    }

📊 Complete Flow Example
User types: "How do neural networks learn from data?"
1. Frontend sends: GET /search?query=how do neural networks learn&mode=auto

2. Backend detects:
   - Mode: AI (detected question)
   - Category: ai_cs (detected "neural networks")

3. Cache check:
   - Search for similar cached queries
   - Found: "neural network training" (similarity: 0.87)
   - ❌ Not similar enough (threshold: 0.90)

4. AI Agent optimizes:
   Original: "how do neural networks learn from data"
   Optimized: "neural network training algorithms"
   Confidence: 0.95

5. Cascading search:
   Try arxiv (primary for ai_cs)
   → Found 45 papers ✅
   → Enough! Stop here

6. Post-processing:
   Deduplicate: 45 → 42 papers
   Semantic rerank: Top 20

7. Cache result for next time

8. Return to user:
   - 20 papers
   - 1 API call
   - 1.8 seconds total
   - Metadata shows full process

✅ Implementation Checklist
Week 1: Core Setup

 Create search_config.py with all sources/categories
 Build UnifiedSearchService class
 Implement category auto-detection
 Add source hierarchy logic

Week 2: Search Modes

 Implement quick search
 Implement AI search with agent
 Add auto mode detection
 Test both modes

Week 3: Optimization

 Add semantic caching
 Implement cascading fallback
 Add deduplication
 Semantic reranking

Week 4: Frontend & Polish

 Build search UI (your choice: 2 bars or 1 smart bar)
 Category dropdown
 Mode toggle (optional)
 Results display
 Testing & optimization


🎯 My Recommendation for UX
Use ONE smart search bar with:

Auto-detection (AI vs quick)
Category dropdown
Optional mode toggle for power users

┌─────────────────────────────────────────────────┐
│ 🔍 Search papers...          [AI & CS ▼]        │
│ ┌─────────────────────────────────────────────┐ │
│ │ How do neural networks learn?    [Search]  │ │
│ └─────────────────────────────────────────────┘ │
│ 💡 AI mode detected - will optimize your query │
│ [⚡ Quick] [🤖 AI ✓] [Auto]                     │
└─────────────────────────────────────────────────┘
This gives users:

✅ Simple default experience
✅ Power user control (mode toggle)
✅ Smart auto-detection
✅ Visual feedback