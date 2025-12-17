import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.arxiv_service import ArxivService
from app.services.semantic_scholar_service import SemanticScholarService
from app.services.openalex_service import OpenAlexService
from app.services.biorxiv_service import bioRxivService
from app.services.core_service import COREService
from app.services.pubmed_service import PubMedService
from app.services.crossref_service import CrossRefService
from app.services.europe_pmc_service import EuropePMCService
from app.services.eric_service import ERICService
from app.services.category_service import CategoryService
from app.services.ai_query_analyzer import AIQueryAnalyzer
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.utils.deduplication import deduplicate_papers
from app.utils.cache import CacheService
from app.models.paper import Paper
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class UnifiedSearchService:
    """Unified search service that queries multiple sources"""
    
    def __init__(
        self,
        cache_service: CacheService,
        vector_service: VectorService,
        semantic_scholar_api_key: Optional[str] = None,
        openalex_email: Optional[str] = None,
        crossref_email: Optional[str] = None
    ):
        """Initialize all search services"""
        self.cache = cache_service
        self.vector_service = vector_service

        # Initialize source services
        self.arxiv = ArxivService()
        self.semantic_scholar = SemanticScholarService(api_key=semantic_scholar_api_key)
        self.openalex = OpenAlexService(email=openalex_email)
        self.biorxiv = bioRxivService()
        self.core = COREService()
        self.pubmed = PubMedService()
        self.crossref = CrossRefService(email=crossref_email)
        self.europe_pmc = EuropePMCService()
        self.eric = ERICService()

        # Initialize category service
        self.category_service = CategoryService()

        # Initialize embedding service for semantic search
        self.embedding_service = EmbeddingService()

        self.sources = [
            self.arxiv, self.semantic_scholar, self.openalex,
            self.biorxiv, self.core, self.pubmed, self.crossref,
            self.europe_pmc, self.eric
        ]
    
    async def search(
        self,
        query: str,
        limit: int = 50,
        sources: Optional[List[str]] = None,
        use_cache: bool = True,
        semantic_rerank: bool = True,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Search papers across multiple sources with semantic reranking

        Args:
            query: Search query string
            limit: Maximum total results to return
            sources: List of sources to search (default: all)
            use_cache: Whether to use cache
            semantic_rerank: Whether to apply semantic reranking

        Returns:
            {
                "papers": [...],
                "total": int,
                "query": str,
                "sources_used": [...],
                "cached": bool
            }
        """
        start_time = time.time()
        debug_info = {
            "query": query,
            "limit": limit,
            "sources_requested": sources,
            "use_cache": use_cache,
            "semantic_rerank": semantic_rerank
        }

        if settings.DEBUG_MODE:
            logger.info(f"🔍 SEARCH START: {debug_info}")

        # Check cache first (with semantic rerank flag)
        cache_start = time.time()
        if use_cache:
            cached = await self.cache.get_search_results(query, limit, semantic_rerank=semantic_rerank)
            if cached:
                cached["cached"] = True
                cache_time = time.time() - cache_start
                if settings.DEBUG_MODE:
                    logger.info(f"⚡ CACHE HIT: Returning {len(cached['papers'])} papers in {cache_time:.2f}s")
                return cached

        cache_time = time.time() - cache_start
        if settings.DEBUG_MODE:
            logger.debug(f"💾 Cache check completed in {cache_time:.2f}s")

        # Determine which sources to use
        active_sources = self._get_active_sources(sources)
        debug_info["active_sources"] = [s.source_name for s in active_sources]

        # Stage 1: Keyword Discovery (cast wide net)
        # Search with higher limit to get more candidates for reranking
        discovery_limit = min(limit * 2, 200)  # Get more papers for better reranking

        if settings.DEBUG_MODE:
            logger.info(f"🌐 API SEARCH: Querying {len(active_sources)} sources for '{query}' (discovery_limit={discovery_limit})")

        api_start = time.time()
        results = await self._parallel_search(query, discovery_limit, active_sources)
        api_time = time.time() - api_start

        total_api_papers = len(results)
        debug_info["api_results"] = {
            "total_papers": total_api_papers,
            "api_time_ms": round(api_time * 1000, 2)
        }

        if settings.DEBUG_MODE:
            logger.info(f"📊 API RESULTS: Found {total_api_papers} papers in {api_time:.2f}s")
            # Count papers per source (this is approximate since results are flattened)
            logger.debug(f"  - Total papers from all sources: {total_api_papers}")

        # Deduplicate papers
        dedup_start = time.time()
        deduplicated = deduplicate_papers(results)
        dedup_time = time.time() - dedup_start

        debug_info["deduplication"] = {
            "input_papers": total_api_papers,
            "output_papers": len(deduplicated),
            "duplicates_removed": total_api_papers - len(deduplicated),
            "dedup_time_ms": round(dedup_time * 1000, 2)
        }

        if settings.DEBUG_MODE:
            logger.info(f"🧹 DEDUPLICATION: {total_api_papers} → {len(deduplicated)} papers ({dedup_time:.2f}s)")

        # Stage 2: Semantic Ranking (find best matches)
        if semantic_rerank and deduplicated:
            # Use provided database session or create a new one
            if db is None:
                db = Session()
                should_close = True
            else:
                should_close = False

            db_start = time.time()
            try:
                if settings.DEBUG_MODE:
                    logger.info(f"🗄️ DATABASE OPERATIONS: Processing {len(deduplicated)} papers")

                # Save new papers to DB and generate embeddings
                db_save_start = time.time()
                saved_papers = await self.save_papers_to_db(deduplicated, db)
                paper_ids = [p.id for p in saved_papers]
                db_save_time = time.time() - db_save_start

                debug_info["database_save"] = {
                    "papers_saved": len(saved_papers),
                    "save_time_ms": round(db_save_time * 1000, 2)
                }

                if settings.DEBUG_MODE:
                    logger.debug(f"💾 Database save: {len(saved_papers)} papers in {db_save_time:.2f}s")

                # Generate embeddings for new papers
                embed_start = time.time()
                self.vector_service.generate_and_store_embeddings(db, paper_ids)
                embed_time = time.time() - embed_start

                debug_info["embedding_generation"] = {
                    "papers_embedded": len(paper_ids),
                    "embed_time_ms": round(embed_time * 1000, 2)
                }

                if settings.DEBUG_MODE:
                    logger.info(f"🧠 Embedding generation: {len(paper_ids)} papers in {embed_time:.2f}s")

                # Try vector search first (papers with embeddings)
                vector_start = time.time()
                vector_results = self.vector_service.semantic_search(
                    db=db,
                    query=query,
                    limit=limit,
                    threshold=0.1  # Low threshold to get broad results
                )
                vector_time = time.time() - vector_start

                debug_info["vector_search"] = {
                    "results_found": len(vector_results) if vector_results else 0,
                    "vector_time_ms": round(vector_time * 1000, 2)
                }

                if settings.DEBUG_MODE:
                    logger.info(f"🔍 Vector search: {len(vector_results) if vector_results else 0} results in {vector_time:.2f}s")

                if vector_results:
                    if settings.DEBUG_MODE:
                        logger.info("✅ Using vector-based ranking")

                    # Get embedded papers from search results that are in deduplicated
                    embedded_papers = {
                        paper['id']: paper for paper in vector_results
                        if paper.get('id') and any(
                            paper['id'] == str(p.get('id', '')) for p in deduplicated
                        )
                    }

                    # For papers without embeddings, do on-the-fly reranking
                    non_embedded = [
                        p for p in deduplicated
                        if not any(paper.get('id') == str(p.get('id', '')) for paper in vector_results)
                    ]

                    debug_info["ranking_breakdown"] = {
                        "vector_ranked": len(embedded_papers),
                        "traditional_ranked": len(non_embedded)
                    }

                    if non_embedded:
                        if settings.DEBUG_MODE:
                            logger.debug(f"🔄 Traditional ranking for {len(non_embedded)} papers without embeddings")

                        trad_start = time.time()
                        non_embedded_reranked = self.embedding_service.rerank_by_semantic_similarity(
                            query=query,
                            papers=non_embedded,
                            top_k=len(non_embedded)  # Keep all non-embedded papers
                        )
                        trad_time = time.time() - trad_start

                        debug_info["traditional_ranking"] = {
                            "papers_ranked": len(non_embedded_reranked),
                            "ranking_time_ms": round(trad_time * 1000, 2)
                        }

                        # Add to embedded results
                        for paper in non_embedded_reranked:
                            if 'id' not in paper:
                                # Handle papers that aren't in DB yet (newly found)
                                embedded_papers[str(id(paper))] = paper

                    reranked_papers = list(embedded_papers.values())
                    # Sort by semantic score (vector search results have it)
                    reranked_papers.sort(key=lambda x: x.get('semantic_score', 0), reverse=True)
                    reranked_papers = reranked_papers[:limit]
                else:
                    if settings.DEBUG_MODE:
                        logger.warning("⚠️ Vector search failed, falling back to traditional ranking")

                    # Fallback to on-the-fly reranking
                    trad_fallback_start = time.time()
                    reranked_papers = self.embedding_service.rerank_by_semantic_similarity(
                        query=query,
                        papers=deduplicated,
                        top_k=limit
                    )
                    trad_fallback_time = time.time() - trad_fallback_start

                    debug_info["fallback_ranking"] = {
                        "method": "traditional_similarity",
                        "papers_ranked": len(reranked_papers),
                        "ranking_time_ms": round(trad_fallback_time * 1000, 2)
                    }

            finally:
                if should_close:
                    db.close()

            db_time = time.time() - db_start
            debug_info["database_total_time_ms"] = round(db_time * 1000, 2)

        else:
            if settings.DEBUG_MODE:
                logger.info("📊 Using citation-based ranking (semantic rerank disabled)")

            # Fallback to citation-based ranking
            reranked_papers = sorted(
                deduplicated,
                key=lambda p: p.get("citation_count", 0),
                reverse=True
            )[:limit]

            debug_info["ranking_method"] = "citation_based"

        # Prepare response
        total_time = time.time() - start_time
        response = {
            "papers": reranked_papers,
            "total": len(reranked_papers),
            "query": query,
            "sources_used": [s.source_name for s in active_sources],
            "cached": False,
            "debug_info": debug_info if settings.DEBUG_MODE else None
        }

        debug_info["total_time_ms"] = round(total_time * 1000, 2)
        debug_info["final_results"] = {
            "papers_returned": len(reranked_papers),
            "cache_used": False
        }

        if settings.DEBUG_MODE:
            logger.info(f"✅ SEARCH COMPLETE: {len(reranked_papers)} papers in {total_time:.2f}s")
            logger.debug(f"📋 Full debug info: {debug_info}")

        # Cache results (with semantic rerank flag)
        if use_cache:
            await self.cache.set_search_results(query, response, limit, semantic_rerank=semantic_rerank)

        return response
    
    async def _parallel_search(
        self,
        query: str,
        limit: int,
        sources: List[Any]
    ) -> List[Dict[str, Any]]:
        """Execute searches in parallel"""
        # Create tasks for each source
        per_source_limit = max(20, limit // len(sources))
        
        tasks = [
            source.search(query, limit=per_source_limit)
            for source in sources
        ]
        
        # Execute in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            print("Search timeout - returning partial results")
            results = []
        
        # Flatten results and filter errors
        all_papers = []
        for result in results:
            if isinstance(result, list):
                all_papers.extend(result)
            elif isinstance(result, Exception):
                print(f"Source error: {str(result)}")
        
        return all_papers
    
    def _get_active_sources(self, source_names: Optional[List[str]] = None) -> List[Any]:
        """Get active source services"""
        if not source_names:
            return self.sources

        source_map = {
            "arxiv": self.arxiv,
            "semantic_scholar": self.semantic_scholar,
            "openalex": self.openalex,
            "biorxiv": self.biorxiv,
            "core": self.core,
            "pubmed": self.pubmed,
            "crossref": self.crossref,
            "europe_pmc": self.europe_pmc,
            "eric": self.eric
        }

        return [source_map[name] for name in source_names if name in source_map]
    
    async def get_paper_by_id(
        self,
        paper_id: str,
        source: str,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """Get a specific paper by ID from a source"""
        # Check database first
        db_paper = self._get_paper_from_db(paper_id, source, db)
        if db_paper:
            return db_paper.to_dict()
        
        # Fetch from source
        source_service = self._get_active_sources([source])
        if not source_service:
            return None
        
        paper_data = await source_service[0].get_paper_by_id(paper_id)
        
        # Save to database
        if paper_data:
            db_paper = self._save_paper_to_db(paper_data, db)
            return db_paper.to_dict() if db_paper else paper_data
        
        return None
    
    def _get_paper_from_db(
        self,
        paper_id: str,
        source: str,
        db: Session
    ) -> Optional[Paper]:
        """Get paper from database"""
        id_field_map = {
            "arxiv": Paper.arxiv_id,
            "semantic_scholar": Paper.semantic_scholar_id,
            "openalex": Paper.openalex_id,
            "biorxiv": Paper.doi,  # bioRxiv uses DOI as primary ID
            "core": Paper.doi      # CORE uses DOI when available
        }

        id_field = id_field_map.get(source)
        if not id_field:
            return None

        return db.query(Paper).filter(id_field == paper_id).first()
    
    def _save_paper_to_db(self, paper_data: Dict[str, Any], db: Session) -> Optional[Paper]:
        """Save paper to database"""
        try:
            # Check if already exists by any ID
            existing = db.query(Paper).filter(
                (Paper.arxiv_id == paper_data.get("arxiv_id")) |
                (Paper.doi == paper_data.get("doi")) |
                (Paper.semantic_scholar_id == paper_data.get("semantic_scholar_id")) |
                (Paper.openalex_id == paper_data.get("openalex_id"))
            ).first()
            
            if existing:
                return existing
            
            # Create new paper
            paper = Paper(
                arxiv_id=paper_data.get("arxiv_id"),
                doi=paper_data.get("doi"),
                semantic_scholar_id=paper_data.get("semantic_scholar_id"),
                openalex_id=paper_data.get("openalex_id"),
                title=paper_data.get("title"),
                abstract=paper_data.get("abstract"),
                authors=paper_data.get("authors"),
                publication_date=paper_data.get("publication_date"),
                pdf_url=paper_data.get("pdf_url"),
                source=paper_data.get("source"),
                citation_count=paper_data.get("citation_count", 0),
                venue=paper_data.get("venue"),
                is_processed=False
            )
            
            db.add(paper)
            db.commit()
            db.refresh(paper)
            
            return paper
            
        except Exception as e:
            db.rollback()
            print(f"Error saving paper: {str(e)}")
            return None
    
    async def save_papers_to_db(
        self,
        papers: List[Dict[str, Any]],
        db: Session
    ) -> List[Paper]:
        """Batch save papers to database"""
        saved = []
        for paper_data in papers:
            paper = self._save_paper_to_db(paper_data, db)
            if paper:
                saved.append(paper)
        return saved

    async def smart_parallel_search(
        self,
        category: str,
        original_query: str,
        limit: int = 50,
        use_cache: bool = True,
        semantic_rerank: bool = True,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Smart parallel search with AI query expansion and rate limit fallbacks

        Args:
            category: Category ID (ai_cs, medicine_biology, etc.)
            original_query: Original user query
            limit: Maximum results to return
            use_cache: Whether to use cache
            semantic_rerank: Whether to apply semantic reranking

        Returns:
            Search results with parallel query execution and fallbacks
        """
        start_time = time.time()

        # Validate category
        if not self.category_service.validate_category(category):
            raise ValueError(f"Invalid category: {category}")

        category_config = self.category_service.get_category(category)
        sources = category_config["sources"]

        if settings.DEBUG_MODE:
            logger.info(f"🎯 SMART PARALLEL SEARCH: {category} | {original_query}")
            logger.info(f"📋 Sources: {sources}")

        # Step 1: AI Query Expansion (generate 2 variations)
        ai_start = time.time()
        ai_analyzer = AIQueryAnalyzer()
        expanded_result = await ai_analyzer.analyze_and_expand_query(original_query)

        # Get queries: original + 2 AI variations
        all_queries = expanded_result["search_queries"][:3]  # [original, variation1, variation2]
        ai_time = time.time() - ai_start

        if settings.DEBUG_MODE:
            logger.info(f"🤖 AI Expansion: {len(all_queries)} queries in {ai_time:.2f}s")
            for i, query in enumerate(all_queries):
                logger.debug(f"   Query {i+1}: {query}")

        # Step 2: Assign queries to sources
        query_source_pairs = list(zip(all_queries, sources))

        if settings.DEBUG_MODE:
            logger.info("🔄 Query-Source Assignment:")
            for query, source in query_source_pairs:
                logger.info(f"   '{query[:50]}...' → {source}")

        # Step 3: Parallel search with fallbacks
        parallel_start = time.time()
        all_results = await self._parallel_search_with_fallbacks(
            query_source_pairs, limit, use_cache, semantic_rerank, db
        )
        parallel_time = time.time() - parallel_start

        # Step 4: Final deduplication and ranking
        final_results = await self._finalize_smart_search_results(
            all_results, original_query, limit, semantic_rerank, db
        )

        total_time = time.time() - start_time

        response = {
            "papers": final_results["papers"],
            "total": len(final_results["papers"]),
            "query": original_query,
            "category": category,
            "sources_used": sources,
            "ai_expanded_queries": all_queries,
            "cached": False,
            "debug_info": {
                "total_time_ms": round(total_time * 1000, 2),
                "ai_expansion_time_ms": round(ai_time * 1000, 2),
                "parallel_search_time_ms": round(parallel_time * 1000, 2),
                "query_count": len(all_queries),
                "source_count": len(sources),
                "results_per_query": final_results.get("results_per_query", {}),
                "fallbacks_activated": final_results.get("fallbacks_activated", 0)
            } if settings.DEBUG_MODE else None
        }

        if settings.DEBUG_MODE:
            logger.info(f"✅ SMART SEARCH COMPLETE: {len(final_results['papers'])} papers in {total_time:.2f}s")

        return response

    async def _parallel_search_with_fallbacks(
        self,
        query_source_pairs: List[tuple],
        limit: int,
        use_cache: bool,
        semantic_rerank: bool,
        db: Optional[Session]
    ) -> List[Dict[str, Any]]:
        """
        Execute parallel searches with intelligent fallbacks for rate limits
        """
        all_results = []
        fallback_activated = False

        # Create primary search tasks (all queries search their assigned sources simultaneously)
        primary_tasks = []
        for query, source in query_source_pairs:
            task = asyncio.create_task(
                self._search_single_source_safe(query, source, limit // len(query_source_pairs))
            )
            primary_tasks.append((query, source, task))

        # Execute all primary searches in parallel
        if settings.DEBUG_MODE:
            logger.info(f"🚀 Starting {len(primary_tasks)} parallel searches")

        primary_results = await asyncio.gather(
            *[task for _, _, task in primary_tasks],
            return_exceptions=True
        )

        # Process results and handle fallbacks
        successful_searches = 0
        failed_searches = []

        for i, result in enumerate(primary_results):
            query, source, _ = primary_tasks[i]

            if isinstance(result, Exception):
                # Rate limit or error occurred
                if settings.DEBUG_MODE:
                    logger.warning(f"❌ Search failed: {source} | {query[:50]}... | Error: {str(result)}")

                failed_searches.append((query, source, str(result)))
                fallback_activated = True
            else:
                # Search succeeded
                papers_found = len(result) if isinstance(result, list) else 0
                successful_searches += 1

                if settings.DEBUG_MODE:
                    logger.info(f"✅ Search success: {source} | {papers_found} papers | {query[:50]}...")

                if isinstance(result, list):
                    all_results.extend(result)

        # Activate fallbacks for failed searches
        if failed_searches and len(query_source_pairs) >= 3:
            if settings.DEBUG_MODE:
                logger.info(f"🔄 Activating fallbacks for {len(failed_searches)} failed searches")

            fallback_results = await self._activate_fallbacks(
                failed_searches, query_source_pairs, limit // len(failed_searches)
            )
            all_results.extend(fallback_results)

        if settings.DEBUG_MODE:
            logger.info(f"📊 Parallel search summary: {successful_searches} success, {len(failed_searches)} failed, {len(all_results)} total papers")

        return all_results

    async def _search_single_source_safe(self, query: str, source: str, limit: int) -> List[Dict[str, Any]]:
        """
        Safely search a single source with error handling
        """
        try:
            # Get source service
            source_services = self._get_active_sources([source])
            if not source_services:
                if settings.DEBUG_MODE:
                    logger.warning(f"No service found for source: {source}")
                return []

            source_service = source_services[0]

            # Execute search
            results = await source_service.search(query, limit=limit)

            # Ensure we return a list
            return results if isinstance(results, list) else []

        except Exception as e:
            # Re-raise exception to be handled by caller
            raise e

    async def _activate_fallbacks(
        self,
        failed_searches: List[tuple],
        all_query_source_pairs: List[tuple],
        limit_per_search: int
    ) -> List[Dict[str, Any]]:
        """
        Activate fallback sources for failed searches
        """
        fallback_results = []

        # Use the third source as backup for all failed searches
        if len(all_query_source_pairs) >= 3:
            backup_source = all_query_source_pairs[2][1]  # Third source

            if settings.DEBUG_MODE:
                logger.info(f"🛟 Using {backup_source} as backup for {len(failed_searches)} failed searches")

            for failed_query, _, _ in failed_searches:
                try:
                    backup_results = await self._search_single_source_safe(
                        failed_query, backup_source, limit_per_search
                    )
                    fallback_results.extend(backup_results)

                    if settings.DEBUG_MODE:
                        logger.info(f"✅ Backup search success: {backup_source} | {len(backup_results)} papers | {failed_query[:50]}...")

                except Exception as backup_error:
                    if settings.DEBUG_MODE:
                        logger.error(f"❌ Backup search also failed: {backup_source} | {str(backup_error)}")

        return fallback_results

    async def _finalize_smart_search_results(
        self,
        all_results: List[Dict[str, Any]],
        original_query: str,
        limit: int,
        semantic_rerank: bool,
        db: Optional[Session]
    ) -> Dict[str, Any]:
        """
        Finalize search results with deduplication and ranking
        """
        # Deduplicate results from all parallel searches
        deduplicated = deduplicate_papers(all_results)

        if settings.DEBUG_MODE:
            logger.info(f"🧹 Deduplication: {len(all_results)} → {len(deduplicated)} papers")

        # Apply semantic reranking if enabled
        if semantic_rerank and deduplicated:
            # Use existing semantic ranking logic
            if db is None:
                db = Session()
                should_close = True
            else:
                should_close = False

            try:
                # Save and embed papers
                saved_papers = await self.save_papers_to_db(deduplicated, db)
                paper_ids = [p.id for p in saved_papers]
                self.vector_service.generate_and_store_embeddings(db, paper_ids)

                # Vector search for ranking
                vector_results = self.vector_service.semantic_search(
                    db=db, query=original_query, limit=limit, threshold=0.1
                )

                if vector_results:
                    # Sort by semantic similarity
                    final_papers = sorted(
                        vector_results,
                        key=lambda x: x.get('semantic_score', 0),
                        reverse=True
                    )[:limit]
                else:
                    # Fallback to citation-based ranking
                    final_papers = sorted(
                        deduplicated,
                        key=lambda p: p.get("citation_count", 0),
                        reverse=True
                    )[:limit]

            finally:
                if should_close:
                    db.close()
        else:
            # Simple citation-based ranking
            final_papers = sorted(
                deduplicated,
                key=lambda p: p.get("citation_count", 0),
                reverse=True
            )[:limit]

        return {
            "papers": final_papers,
            "total_raw_results": len(all_results),
            "total_deduplicated": len(deduplicated)
        }
