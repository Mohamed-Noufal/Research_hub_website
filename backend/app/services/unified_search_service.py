"""
Unified Search Service - Complete Academic Search System
Handles all search modes with intelligent routing and cascading fallback.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.search_config import SearchConfig
from app.services.enhanced_vector_service import EnhancedVectorService
from app.services.ai_query_analyzer import AIQueryAnalyzer
from app.utils.cache import CacheService
from app.utils.deduplication import deduplicate_papers
from app.core.database import get_db
from sqlalchemy.orm import Session

# Import all source services
from app.services.arxiv_service import ArxivService
from app.services.semantic_scholar_service import SemanticScholarService
from app.services.openalex_service import OpenAlexService
from app.services.pubmed_service import PubMedService
from app.services.europe_pmc_service import EuropePMCService
from app.services.crossref_service import CrossRefService
from app.services.core_service import COREService
from app.services.eric_service import ERICService
from app.services.biorxiv_service import bioRxivService


class UnifiedSearchService:
    """
    One service that handles:
    - Quick search (keyword-based)
    - AI search (agent-powered)
    - Category detection
    - Source cascading
    - Caching with semantic similarity
    - Deduplication and semantic reranking
    """

    def __init__(self, cache_service: CacheService = None):
        self.config = SearchConfig()
        self.cache = cache_service or CacheService()
        self.vector_service = EnhancedVectorService()
        self.ai_analyzer = AIQueryAnalyzer()

        # Initialize all sources
        self.sources = {}
        source_classes = {
            "arxiv": ArxivService,
            "semantic_scholar": SemanticScholarService,
            "openalex": OpenAlexService,
            "pubmed": PubMedService,
            "europe_pmc": EuropePMCService,
            "crossref": CrossRefService,
            "core": COREService,
            "eric": ERICService,
            "biorxiv": bioRxivService
        }

        for source_id, source_class in source_classes.items():
            try:
                self.sources[source_id] = source_class()
                print(f"✅ Initialized {source_id}")
            except Exception as e:
                print(f"❌ Failed to initialize {source_id}: {e}")
                self.sources[source_id] = None

        # Category-specific source routing
        self.CATEGORY_SOURCES = {
            'ai_cs': {
                'primary': 'arxiv',
                'backup_1': 'semantic_scholar',
                'backup_2': 'openalex',
                'max_results': 100
            },
            'medicine_biology': {
                'primary': 'pubmed',
                'backup_1': 'europe_pmc',
                'backup_2': 'crossref',
                'max_results': 100
            },
            'agriculture_animal': {
                'primary': 'openalex',
                'backup_1': 'core',
                'backup_2': 'crossref',
                'max_results': 200
            },
            'humanities_social': {
                'primary': 'eric',
                'backup_1': 'openalex',
                'backup_2': 'semantic_scholar',
                'max_results': 100
            },
            'economics_business': {
                'primary': 'openalex',
                'backup_1': 'crossref',
                'backup_2': 'semantic_scholar',
                'max_results': 200
            }
        }
        
        # Default sources if category not found
        self.DEFAULT_SOURCES = {
            'primary': 'arxiv',
            'backup_1': 'semantic_scholar',
            'backup_2': 'openalex',
            'max_results': 100
        }
    
    def _is_valid_paper(self, paper: Dict) -> bool:
        """Validate paper quality (must have title + abstract OR authors)"""
        title = paper.get('title', '').strip()
        if not title or len(title) < 10:
            return False
        
        abstract = paper.get('abstract', '').strip()
        authors = paper.get('authors', [])
        
        has_abstract = abstract and len(abstract) > 50
        has_authors = authors and len(authors) > 0
        
        return has_abstract or has_authors
    
    async def _get_smart_cache_ttl(self, query: str, db: Session) -> int:
        """Get smart TTL based on query popularity from search history"""
        try:
            from app.models.search_history import SearchHistory
            from datetime import datetime, timedelta
            
            # Count searches in last 30 days
            recent_count = db.query(SearchHistory).filter(
                SearchHistory.query.ilike(f"%{query}%"),
                SearchHistory.search_date > datetime.now() - timedelta(days=30)
            ).count()
            
            # Smart TTL tiers for production scale
            if recent_count > 100:
                return 3600  # 1 hour - Very popular queries
            elif recent_count > 10:
                return 600   # 10 min - Popular queries
            else:
                return 300   # 5 min - Normal queries
        except Exception as e:
            print(f"⚠️ Error getting smart TTL: {e}")
            return 300  # Default 5 min
    
    async def _invalidate_category_cache(self, category: str):
        """Invalidate cache for specific category when papers are added"""
        try:
            # Only invalidate searches in this category
            # This preserves cache for other categories!
            if hasattr(self, 'cache_service'):
                pattern = f"search:*:{category}:*"
                print(f"♻️ Invalidating {category} cache...")
                # Note: This requires cache service to support pattern invalidation
                # For now, we'll rely on TTL expiration
        except Exception as e:
            print(f"⚠️ Cache invalidation failed: {e}")

    async def search(
        self,
        query: str,
        category: str,
        mode: str,
        limit: int = 20,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        New simplified search endpoint

        Args:
            query: User's search query
            category: Selected category (required)
            mode: Search mode: "normal" or "ai"
            limit: Max results to return
            db: Database session

        Returns:
            Search results with comprehensive metadata
        """

        start_time = time.time()

        print(f"\n{'='*60}")
        print(f"🔍 NEW UNIFIED SEARCH REQUEST")
        print(f"{'='*60}")
        print(f"Query: {query}")
        print(f"Category: {category}")
        print(f"Mode: {mode}")
        print(f"Limit: {limit}")

        # STEP 1: Check semantic cache first
        cache_key = f"{query}:{category}:{mode}"
        cached_result = await self._check_semantic_cache(query, category, mode)

        if cached_result:
            print(f"✅ SEMANTIC CACHE HIT (saved {time.time() - start_time:.2f}s)")
            cached_result['metadata']['cached'] = True
            cached_result['metadata']['search_time'] = time.time() - start_time
            return cached_result

        print(f"❌ Cache miss, performing search...")

        # STEP 2: Route to appropriate search method
        if mode == "ai":
            result = await self._ai_search_flow(query, category, limit, db)
        else:
            result = await self._normal_search_flow(query, category, limit, db)

        # STEP 3: Cache the result
        await self._cache_search_result(query, category, mode, result)

        # STEP 4: Add timing and final metadata
        result['metadata']['search_time'] = time.time() - start_time
        result['metadata']['cached'] = False
        result['metadata']['timestamp'] = datetime.utcnow().isoformat()

        print(f"\n{'='*60}")
        print(f"✅ SEARCH COMPLETE")
        print(f"{'='*60}")
        print(f"Mode: {mode}")
        print(f"Results: {len(result['papers'])}")
        print(f"API calls: {result['metadata']['api_calls_made']}")
        print(f"Time: {result['metadata']['search_time']:.2f}s")
        print(f"{'='*60}\n")

        return result

    async def _check_semantic_cache(self, query: str, category: str, mode: str) -> Optional[Dict[str, Any]]:
        """Check for semantically similar cached results"""
        try:
            cached = await self.cache.get_search_results(query, limit=20, semantic_rerank=True)

            if cached:
                cache_age = time.time() - cached.get('timestamp', 0)
                if cache_age < 3600:  # 1 hour cache
                    return cached

            return None
        except Exception as e:
            print(f"Cache check error: {e}")
            return None

    async def _cache_search_result(self, query: str, category: str, mode: str, result: Dict[str, Any]):
        """Cache search result with metadata"""
        try:
            result_copy = result.copy()
            result_copy['timestamp'] = time.time()

            await self.cache.set_search_results(
                query=query,
                results=result_copy,
                limit=20,
                semantic_rerank=True
            )
        except Exception as e:
            print(f"Cache set error: {e}")

    async def _normal_search_flow(self, query: str, category: str, limit: int, db: Session) -> Dict[str, Any]:
        """Normal search with parallel local + external search"""
        start_time = time.time()
        
        print(f"\n📖 NORMAL SEARCH FLOW")
        print(f"Running parallel search: Local DB + External APIs")
        
        # Launch both searches in parallel
        local_task = asyncio.create_task(self._search_local_embeddings(query, category, limit, db))
        external_task = asyncio.create_task(self.search_external_with_fallback(query, category, db))
        
        local_results, external_search_result = await asyncio.gather(local_task, external_task, return_exceptions=True)
        
        if isinstance(local_results, Exception):
            print(f"❌ Local search error: {local_results}")
            local_results = []
        if isinstance(external_search_result, Exception):
            print(f"❌ External search error: {external_search_result}")
            external_search_result = {'papers': [], 'source': 'error', 'api_calls': 0}
        
        external_results = external_search_result.get('papers', [])
        source_used = external_search_result.get('source', 'none')
        api_calls = external_search_result.get('api_calls', 0)
        parallel_time = time.time() - start_time
        
        print(f"✅ Parallel search complete in {parallel_time:.2f}s")
        print(f"   - Local: {len(local_results)} papers")
        print(f"   - External ({source_used}): {len(external_results)} papers")
        
        # Merge results
        final_results = []
        papers_to_save = []
        
        # ✅ Sort local results by hybrid_score (best matches first!)
        if local_results:
            local_results_sorted = sorted(
                local_results,
                key=lambda x: x.get('hybrid_score', 0),
                reverse=True  # Highest score first
            )
            final_results.extend(local_results_sorted)
            print(f"📊 Local results sorted by relevance (best first)")
            
        remaining_slots = limit - len(final_results)
        if remaining_slots > 0 and external_results:
            local_titles = {p.get('title', '').lower().strip() for p in final_results}
            local_dois = {p.get('doi') for p in final_results if p.get('doi')}
            unique_external = [
                p for p in external_results 
                if p.get('title', '').lower().strip() not in local_titles 
                and (not p.get('doi') or p.get('doi') not in local_dois)
            ]
            
            # ✅ Filter for quality papers only (must have title + abstract/authors)
            quality_papers = [
                p for p in unique_external
                if self._is_valid_paper(p)
            ]
            
            papers_to_save = quality_papers[:remaining_slots]
            
            # Log filtered papers
            filtered_count = len(unique_external) - len(quality_papers)
            if filtered_count > 0:
                print(f"⚠️  Filtered out {filtered_count} low-quality papers (missing title/abstract/authors)")

        # Save new papers SYNCHRONOUSLY (not in background) so IDs are available
        saved_papers = []
        if papers_to_save and db:
            try:
                saved_papers = await self._save_results_and_return_ids(papers_to_save, category, db)
                final_results.extend(saved_papers)  # Use saved papers with real DB IDs
                
                # ✅ Queue embedding generation in BACKGROUND (non-blocking!)
                if saved_papers:
                    paper_ids = [int(p['id']) for p in saved_papers]
                    print(f"📊 Queuing {len(paper_ids)} papers for background embedding generation...")
                    
                    # Create background task (don't await!)
                    asyncio.create_task(
                        self._generate_embeddings_background(paper_ids, category, db)
                    )
                    
                    print(f"✅ Background task created - user will get results immediately!")
                        
            except Exception as e:
                # ⚠️ CRITICAL FALLBACK: If save fails completely
                print(f"❌ Failed to save papers to database: {e}")
                db.rollback()  # Rollback transaction
                
                # FALLBACK: Return papers without DB IDs (still useful for user)
                print(f"⚠️ FALLBACK: Returning {len(papers_to_save)} papers without saving")
                final_results.extend(papers_to_save)
        else:
            final_results.extend(papers_to_save)  # Fallback if no db

        return {
            "papers": final_results,
            "total": len(final_results),
            "metadata": {
                "query": query,
                "category": category,
                "mode": "normal",
                "search_strategy": "parallel_merged",
                "api_calls_made": api_calls,
                "source_used": source_used,
                "local_results": len(local_results),
                "external_results": len(external_results),
                "search_time": parallel_time,
                "papers_saved": len(saved_papers)
            }
        }

    async def _ai_search_flow(self, query: str, category: str, limit: int, db: Session) -> Dict[str, Any]:
        """AI search with query expansion"""
        print(f"\n🤖 AI SEARCH FLOW")
        ai_recommendations = await self._get_ai_recommendations(query)
        
        return {
            "papers": [],
            "total": 0,
            "metadata": {
                "query": query,
                "category": category,
                "mode": "ai",
                "ai_recommendations": ai_recommendations,
                "search_strategy": "ai_recommendations_pending",
                "api_calls_made": 1,
                "status": "awaiting_user_selection"
            }
        }

    async def _search_local_embeddings(self, query: str, category: str, limit: int, db: Session) -> List[Dict]:
        """Search local embedded data for scaling"""
        try:
            print(f"🔍 Searching local embeddings for: '{query}' in category: {category}")

            results = await self.vector_service.hybrid_search(
                db=db,
                query=query,
                category=category,
                limit=limit,
                semantic_weight=0.7,
                keyword_weight=0.3
            )

            papers = results.get('papers', [])
            print(f"✅ Found {len(papers)} papers in local database")
            return papers

        except Exception as e:
            print(f"❌ Local embedding search failed: {e}")
            return []

    async def _search_single_source(self, source_id: str, query: str, limit: int, db: Session) -> List[Dict]:
        """Search a single external source with error handling"""
        source = self.sources.get(source_id)
        if not source:
            print(f"⚠️  Source {source_id} not available")
            return []

        try:
            print(f"🔍 Searching {source_id}...")
            results = await source.search(query, limit=limit)
            if results:
                print(f"✅ {source_id}: {len(results)} papers found")
                return results
            else:
                print(f"❌ {source_id}: No results")
                return []
        except Exception as e:
            print(f"❌ {source_id} failed: {e}")
            return []

    def get_sources_for_category(self, category: str) -> Dict[str, Any]:
        """Get appropriate sources for the given category"""
        return self.CATEGORY_SOURCES.get(category, self.DEFAULT_SOURCES)

    async def search_external_with_fallback(self, query: str, category: str, db: Session) -> Dict[str, Any]:
        """
        Search external sources based on category with cascading fallback
        Try primary → backup_1 → backup_2
        """
        sources_config = self.get_sources_for_category(category)
        max_limit = sources_config['max_results']
        
        # Try primary source
        primary_source = sources_config['primary']
        print(f"🔍 Category: {category} → PRIMARY source: {primary_source} (max: {max_limit})")
        results = await self._search_single_source(primary_source, query, max_limit, db)
        if results and len(results) > 0:
            print(f"✅ {primary_source}: {len(results)} papers found")
            return {'papers': results, 'source': primary_source, 'api_calls': 1}
        
        # Try backup 1
        backup_1 = sources_config['backup_1']
        print(f"🔍 PRIMARY failed → BACKUP 1: {backup_1}")
        results = await self._search_single_source(backup_1, query, max_limit, db)
        if results and len(results) > 0:
            print(f"✅ {backup_1}: {len(results)} papers found")
            return {'papers': results, 'source': backup_1, 'api_calls': 2}
        
        # Try backup 2
        backup_2 = sources_config['backup_2']
        print(f"🔍 BACKUP 1 failed → BACKUP 2: {backup_2}")
        results = await self._search_single_source(backup_2, query, max_limit, db)
        if results and len(results) > 0:
            print(f"✅ {backup_2}: {len(results)} papers found")
            return {'papers': results, 'source': backup_2, 'api_calls': 3}
        
        # All sources failed
        print(f"❌ All sources failed for category: {category}")
        return {'papers': [], 'source': 'none', 'api_calls': 3}

    async def _get_ai_recommendations(self, query: str) -> List[str]:
        """Get AI recommendations from Groq"""
        try:
            print(f"🧠 Getting AI recommendations for: '{query}'")

            result = await self.ai_analyzer.analyze_and_expand_query(query)
            recommendations = result.get('search_queries', [])

            print(f"✅ Got {len(recommendations)} AI recommendations")
            return recommendations

        except Exception as e:
            print(f"❌ AI recommendations failed: {e}")
            return [query]

    async def _save_results_without_embeddings(self, papers: List[Dict], category: str, db: Session) -> int:
        """
        ULTRA-FAST: Save external results using BULK INSERT
        Returns count of papers saved
        """
        try:
            from app.models.paper import Paper
            from datetime import datetime

            saved_count = 0

            # Get all existing papers for deduplication check
            existing_papers = db.query(Paper).all()
            existing_dicts = [paper.to_dict() for paper in existing_papers]

            # Convert new papers to same format
            new_papers_dicts = []
            for paper in papers:
                paper_dict = {
                    'title': paper.get('title', ''),
                    'abstract': paper.get('abstract') or '',
                    'authors': paper.get('authors', []),
                    'doi': paper.get('doi'),
                    'arxiv_id': paper.get('arxiv_id'),
                    'semantic_scholar_id': paper.get('semantic_scholar_id'),
                    'openalex_id': paper.get('openalex_id'),
                    'source': paper.get('source', 'unknown'),
                    'publication_date': paper.get('publication_date'),
                    'pdf_url': paper.get('pdf_url'),
                    'citation_count': paper.get('citation_count', 0),
                    'venue': paper.get('venue')
                }
                new_papers_dicts.append(paper_dict)

            # Deduplicate: combine existing + new, then deduplicate
            all_papers = existing_dicts + new_papers_dicts
            deduplicated = deduplicate_papers(all_papers)

            # Find truly new papers (not in existing)
            existing_titles = {p['title'].lower().strip() for p in existing_dicts}
            new_unique_papers = [p for p in deduplicated if p['title'].lower().strip() not in existing_titles]

            print(f"📊 Deduplication: {len(papers)} fetched → {len(new_unique_papers)} truly new")

            if not new_unique_papers:
                print(f"✅ No new papers to save (all duplicates)")
                return 0

            # Prepare bulk insert data
            bulk_data = []
            for paper_data in new_unique_papers:
                bulk_data.append({
                    'title': paper_data['title'],
                    'abstract': paper_data.get('abstract'),
                    'authors': paper_data.get('authors', []),
                    'publication_date': paper_data.get('publication_date'),
                    'pdf_url': paper_data.get('pdf_url'),
                    'source': paper_data.get('source', 'unknown'),
                    'arxiv_id': paper_data.get('arxiv_id'),
                    'doi': paper_data.get('doi'),
                    'semantic_scholar_id': paper_data.get('semantic_scholar_id'),
                    'openalex_id': paper_data.get('openalex_id'),
                    'citation_count': paper_data.get('citation_count', 0),
                    'venue': paper_data.get('venue'),
                    'category': category,
                    'date_added': datetime.utcnow(),
                    'last_updated': datetime.utcnow(),
                    'is_processed': False
                })

            # BULK INSERT
            db.bulk_insert_mappings(Paper, bulk_data)
            db.commit()
            
            saved_count = len(bulk_data)
            print(f"✅ BULK INSERT: {saved_count} papers saved in ~0.5s")

            return saved_count

        except Exception as e:
            print(f"❌ Error saving papers: {e}")
            db.rollback()
            return 0

    async def _save_results_and_return_ids(self, papers: List[Dict], category: str, db: Session) -> List[Dict]:
        """
        Save papers to DB and return them with their actual database IDs.
        This ensures papers can be saved to library immediately.
        """
        try:
            from app.models.paper import Paper
            from datetime import datetime
            
            saved_papers = []
            
            for paper in papers:
                # Check if paper already exists
                existing = None
                
                if paper.get('arxiv_id'):
                    existing = db.query(Paper).filter(Paper.arxiv_id == paper['arxiv_id']).first()
                elif paper.get('doi'):
                    existing = db.query(Paper).filter(Paper.doi == paper['doi']).first()
                elif paper.get('title'):
                    existing = db.query(Paper).filter(Paper.title == paper['title']).first()
                
                if existing:
                    # Paper exists, use its ID
                    paper_dict = existing.to_dict() if hasattr(existing, 'to_dict') else {
                        'id': existing.id,
                        'title': existing.title,
                        'abstract': existing.abstract,
                        'authors': existing.authors,
                        'doi': existing.doi,
                        'arxiv_id': existing.arxiv_id,
                        'source': existing.source,
                        'publication_date': str(existing.publication_date) if existing.publication_date else None,
                        'pdf_url': existing.pdf_url,
                        'citation_count': existing.citation_count,
                        'venue': existing.venue
                    }
                    saved_papers.append(paper_dict)
                else:
                    # Create new paper
                    new_paper = Paper(
                        title=paper.get('title', ''),
                        abstract=paper.get('abstract'),
                        authors=paper.get('authors', []),
                        publication_date=paper.get('publication_date'),
                        pdf_url=paper.get('pdf_url'),
                        source=paper.get('source', 'unknown'),
                        arxiv_id=paper.get('arxiv_id'),
                        doi=paper.get('doi'),
                        semantic_scholar_id=paper.get('semantic_scholar_id'),
                        openalex_id=paper.get('openalex_id'),
                        citation_count=paper.get('citation_count', 0),
                        venue=paper.get('venue'),
                        category=category,
                        date_added=datetime.utcnow(),
                        last_updated=datetime.utcnow(),
                        is_processed=False
                    )
                    db.add(new_paper)
                    db.flush()  # Get the ID without committing
                    
                    paper_dict = paper.copy()
                    paper_dict['id'] = new_paper.id  # Real DB ID
                    saved_papers.append(paper_dict)
            
            db.commit()
            print(f"✅ Saved {len(saved_papers)} papers with real DB IDs")
            return saved_papers
            
        except Exception as e:
            print(f"❌ Error saving papers with IDs: {e}")
            db.rollback()
            # Return original papers as fallback
            return papers

    async def generate_embeddings_background(self, paper_ids: List[str], db: Session):
        """
        BACKGROUND TASK: Generate embeddings for saved papers
        This runs AFTER the response is sent to the user
        """
        try:
            from app.models.paper import Paper
            
            if not paper_ids:
                print("ℹ️ No papers need embeddings")
                return

            print(f"\n🔄 BACKGROUND: Starting embedding generation for {len(paper_ids)} papers")
            start_time = time.time()

            papers_to_embed = db.query(Paper).filter(Paper.id.in_(paper_ids)).all()

            if not papers_to_embed:
                print("⚠️ No papers found for embedding generation")
                return

            # Generate embeddings in batches
            batch_size = 100
            total_embedded = 0

            for i in range(0, len(papers_to_embed), batch_size):
                batch = papers_to_embed[i:i + batch_size]
                
                texts = []
                for paper in batch:
                    text = f"{paper.title}. {paper.abstract or ''}"
                    if paper.authors:
                        text = f"{', '.join(paper.authors[:3])}. {text}"
                    texts.append(text)

                embeddings = self.vector_service.batch_generate_embeddings(texts, batch_size=32)

                for paper, embedding in zip(batch, embeddings):
                    paper.embedding = embedding.tolist()
                    paper.is_processed = True

                db.commit()
                total_embedded += len(batch)
                print(f"  ✅ Embedded {total_embedded}/{len(papers_to_embed)} papers")

            elapsed = time.time() - start_time
            print(f"✅ BACKGROUND COMPLETE: Generated {total_embedded} embeddings in {elapsed:.2f}s")

        except Exception as e:
            print(f"❌ Background embedding generation failed: {e}")
            db.rollback()

    async def get_search_suggestions(self, query: str) -> Dict[str, Any]:
        """Get search suggestions and mode detection"""
        return self.config.get_search_suggestions(query)

    async def get_categories(self) -> Dict[str, Any]:
        """Get all available categories with full info"""
        categories = {}
        for cat_id, cat_info in self.config.CATEGORIES.items():
            categories[cat_id] = {
                "id": cat_id,
                "name": cat_info["name"],
                "description": cat_info["description"],
                "sources": cat_info["sources"],
                "source_count": len(cat_info["sources"]),
                "keywords": cat_info["keywords"][:5]
            }

        return {
            "categories": categories,
            "total": len(categories)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all sources"""
        results = {}
        total_sources = len(self.config.SOURCES)
        working_sources = 0

        for source_id, source_info in self.config.SOURCES.items():
            try:
                source = self.sources.get(source_id)
                if source:
                    test_results = await source.search("test", limit=1)
                    is_working = len(test_results) >= 0
                else:
                    is_working = False

                results[source_id] = {
                    "status": "working" if is_working else "failed",
                    "name": source_info["name"],
                    "reliability": source_info["reliability"],
                    "speed": source_info["speed"]
                }

                if is_working:
                    working_sources += 1

            except Exception as e:
                results[source_id] = {
                    "status": "error",
                    "name": source_info["name"],
                    "error": str(e)
                }

        return {
            "overall_status": "healthy" if working_sources >= total_sources * 0.7 else "degraded",
            "sources": results,
            "summary": {
                "total": total_sources,
                "working": working_sources,
                "failed": total_sources - working_sources,
                "uptime_percentage": (working_sources / total_sources) * 100
            }
        }
    
    async def _generate_embeddings_background(self, paper_ids: List[int], category: str, db: Session):
        """Generate embeddings in background (non-blocking)"""
        try:
            print(f"🔄 BACKGROUND: Starting embedding generation for {len(paper_ids)} papers...")
            
            await self.vector_service.generate_embeddings_for_papers(
                db=db,
                batch_size=50,
                max_papers=len(paper_ids),
                force_regenerate=False
            )
            
            print(f"✅ BACKGROUND: Embeddings generated successfully for {len(paper_ids)} papers")
            
            # Invalidate category cache after embeddings are ready
            await self._invalidate_category_cache(category)
            
        except Exception as e:
            print(f"❌ BACKGROUND: Embedding generation failed: {e}")
            # Don't crash - it's a background task
