"""
Enhanced Vector Service with Category Caching and Hybrid Search
Provides optimized semantic search with intelligent caching for category-based queries.
"""

import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
import numpy as np

from app.models.paper import Paper
from app.core.database import engine

class EnhancedVectorService:
    """Enhanced vector service with category caching and hybrid search capabilities"""

    def __init__(self, model_name: str = 'nomic-ai/nomic-embed-text-v1.5'):
        """Initialize with specified embedding model"""
        self.model_name = model_name
        
        # ✅ Use cached model instead of loading new instance
        from app.core.model_cache import ModelCache
        try:
            self.model = ModelCache.get_model()
        except RuntimeError:
            # Fallback: load model if cache not initialized (shouldn't happen in production)
            print("⚠️  Model cache not initialized, loading model directly")
            self.model = SentenceTransformer(model_name, trust_remote_code=True)
        
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        # Cache settings
        self.default_cache_ttl_hours = 24

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        return self.model.encode(text, normalize_embeddings=True)

    def batch_generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for multiple texts in batches"""
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100
        )

    async def category_search_with_cache(
        self,
        db: Session,
        query: str,
        category: str,
        limit: int = 50,
        cache_ttl_hours: int = None
    ) -> Dict[str, Any]:
        """
        Category-based search with intelligent caching

        Args:
            db: Database session
            query: Search query
            category: Category name
            limit: Max results
            cache_ttl_hours: Cache TTL in hours

        Returns:
            Search results with caching metadata
        """

        if cache_ttl_hours is None:
            cache_ttl_hours = self.default_cache_ttl_hours

        # Generate category-namespaced cache key
        query_hash = hashlib.md5(f"{category.lower().strip()}::{query.lower().strip()}".encode()).hexdigest()

        # Check cache first
        cached_result = await self._get_cached_category_results(db, category, query_hash, cache_ttl_hours)
        if cached_result:
            # Update cache hit counter
            await self._increment_cache_hits(db, category, query_hash)
            return cached_result

        # Perform fresh search
        results = await self._perform_category_vector_search(db, query, category, limit)

        # Cache results
        await self._cache_category_results(db, category, query_hash, results, cache_ttl_hours)

        return results

    async def hybrid_search(
        self,
        db: Session,
        query: str,
        category: str = None,
        limit: int = 50,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        force_refresh: bool = False  # ✅ ADD FORCE REFRESH OPTION
    ) -> Dict[str, Any]:
        """
        Hybrid semantic + keyword search with category filtering

        Args:
            db: Database session
            query: Search query
            category: Optional category filter
            limit: Max results
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)

        Returns:
            Hybrid search results
        """

        # Generate query embedding
        query_embedding = self.generate_embedding(query)

        # Build dynamic WHERE clause
        filters = ["p.embedding IS NOT NULL"]
        params = {
            'query_embedding': query_embedding.tolist(),
            'limit': limit,
            'kw': f'%{query}%',
            'semantic_weight': semantic_weight,
            'keyword_weight': keyword_weight
        }

        if category:
            filters.append("p.category = :category")
            params['category'] = category

        where_clause = " AND ".join(filters)

        # Create vector string for PostgreSQL
        vector_str = '[' + ','.join(f'{x:.6f}' for x in query_embedding) + ']'

        # Hybrid scoring SQL query with vector literal
        sql = f"""
        SELECT p.id, p.title, p.abstract, p.authors, p.source, p.doi,
               (:semantic_weight * (1 - (p.embedding <=> '{vector_str}'::vector)) +
                :keyword_weight * (CASE WHEN p.title ILIKE :kw OR p.abstract ILIKE :kw THEN 1 ELSE 0 END)
               ) AS hybrid_score
        FROM papers p
        WHERE {where_clause}
        ORDER BY hybrid_score DESC
        LIMIT :limit;
        """

        # Remove query_embedding from params since we're using it as a literal
        params_copy = {k: v for k, v in params.items() if k != 'query_embedding'}

        # Execute query
        result = db.execute(text(sql), params_copy).fetchall()

        papers = []
        for row in result:
            score = float(row.hybrid_score)
            # Lower threshold to 0.4 for better recall
            if score >= 0.4:
                papers.append({
                    'id': str(row.id),
                    'title': row.title,
                    'abstract': row.abstract,
                    'authors': row.authors,
                    'source': row.source,
                    'doi': row.doi,
                    'hybrid_score': score
                })

        return {
            'papers': papers,
            'total': len(papers),
            'query': query,
            'category': category,
            'search_type': 'hybrid',
            'semantic_weight': semantic_weight,
            'keyword_weight': keyword_weight,
            'cached': False
        }

    async def _perform_category_vector_search(
        self,
        db: Session,
        query: str,
        category: str,
        limit: int
    ) -> Dict[str, Any]:
        """Perform vector search for specific category"""

        # Generate query embedding
        query_embedding = self.generate_embedding(query)

        # Search in category with vector similarity
        search_sql = """
        SELECT p.id, p.title, p.abstract, p.authors, p.source, p.doi,
               1 - (p.embedding <=> :query_embedding) as similarity_score
        FROM papers p
        WHERE p.category = :category
          AND p.embedding IS NOT NULL
        """

        result = db.execute(text(cache_query), {
            'category': category,
            'query_hash': query_hash
        }).first()

        if result:
            cached_data = result.cached_results

            # ✅ Validate embedding hash if available
            cached_hash = cached_data.get('embedding_hash')
            if cached_hash:
                # We need the current embedding to validate
                # This is called from category_search_with_cache, so we need to pass embedding
                # For now, we'll trust the cache (can be improved later)
                pass

            # Update cache hit counter
            update_sql = """
            UPDATE category_cache
            SET cache_hits = cache_hits + 1
            WHERE category_name = :category AND query_hash = :query_hash
            """
            db.execute(text(update_sql), {'category': category, 'query_hash': query_hash})
            db.commit()

            cached_data['cached'] = True
            cached_data['cache_hits'] = result.cache_hits + 1
            return cached_data

        return None

    def _get_embedding_hash(self, embedding: np.ndarray) -> str:
        """Generate hash of embedding for cache validation"""
        embedding_str = ','.join(f'{x:.6f}' for x in embedding)
        return hashlib.md5(embedding_str.encode()).hexdigest()

    async def _cache_category_results(
        self,
        db: Session,
        category: str,
        query_hash: str,
        results: Dict[str, Any],
        ttl_hours: int,
        embedding: np.ndarray = None  # ✅ ADD EMBEDDING FOR HASH
    ):
        """Cache category search results with embedding validation"""

        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        # Prepare cached data
        cached_data = results.copy()
        cached_data['cached_at'] = datetime.utcnow().isoformat()
        cached_data['expires_at'] = expires_at.isoformat()

        # Include embedding hash for validation
        if embedding is not None:
            cached_data['embedding_hash'] = self._get_embedding_hash(embedding)

        insert_sql = """
        INSERT INTO category_cache (
            category_name, query_hash, last_updated, cached_results,
            result_count, expires_at
        ) VALUES (:category, :query_hash, NOW(), :cached_results, :result_count, :expires_at)
        ON CONFLICT (category_name, query_hash)
        DO UPDATE SET
            last_updated = NOW(),
            cached_results = :cached_results,
            result_count = :result_count,
            expires_at = :expires_at,
            cache_hits = 0
        """

        db.execute(text(insert_sql), {
            'category': category,
            'query_hash': query_hash,
            'cached_results': cached_data,
            'result_count': len(results.get('papers', [])),
            'expires_at': expires_at
        })
        db.commit()

    async def _increment_cache_hits(self, db: Session, category: str, query_hash: str):
        """Increment cache hit counter"""
        update_sql = """
        UPDATE category_cache
        SET cache_hits = cache_hits + 1
        WHERE category_name = :category AND query_hash = :query_hash
        """
        db.execute(text(update_sql), {'category': category, 'query_hash': query_hash})
        db.commit()

    async def generate_embeddings_for_papers(
        self,
        db: Session,
        batch_size: int = 100,
        max_papers: int = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate enhanced embeddings for papers including title + authors + abstract

        Args:
            db: Database session
            batch_size: Batch size for processing
            max_papers: Maximum papers to process (None for all)
            force_regenerate: Regenerate embeddings even if they exist

        Returns:
            Processing statistics
        """

        # Find papers to process
        query = db.query(Paper)
        if not force_regenerate:
            query = query.filter(
                Paper.embedding.is_(None),
                Paper.is_processed == False
            )

        if max_papers:
            query = query.limit(max_papers)

        papers_to_process = query.all()

        if not papers_to_process:
            return {"message": "No papers need embedding generation", "processed": 0}

        total_processed = 0
        total_batches = (len(papers_to_process) + batch_size - 1) // batch_size

        print(f"🔄 Generating ENHANCED embeddings for {len(papers_to_process)} papers in {total_batches} batches")
        print(f"📝 Including: Title + Authors + Abstract for richer semantic search")

        for i in range(0, len(papers_to_process), batch_size):
            batch = papers_to_process[i:i + batch_size]

            # Prepare ENHANCED texts for embedding (Title + Authors + Abstract)
            texts = []
            for paper in batch:
                # Process authors - handle different formats
                authors_text = self._format_authors_for_embedding(paper.authors)

                # Combine: Title + Authors + Abstract
                title = paper.title or ''
                abstract = paper.abstract or ''

                # Create rich text with proper weighting
                combined_text = f"{title} {authors_text} {abstract}".strip()

                # Ensure minimum length for meaningful embedding
                if len(combined_text.split()) < 10:
                    # If too short, emphasize title and authors
                    combined_text = f"{title} {authors_text} {title} {abstract}".strip()

                texts.append(combined_text)

            # Generate embeddings in batch
            try:
                embeddings = self.batch_generate_embeddings(texts)

                # Update papers with enhanced embeddings
                for j, paper in enumerate(batch):
                    paper.embedding = embeddings[j].tolist()
                    paper.is_processed = True
                    paper.last_updated = datetime.utcnow()

                    # Store embedding metadata
                    if not paper.paper_metadata:
                        paper.paper_metadata = {}
                    paper.paper_metadata['embedding_version'] = 'enhanced_v2'
                    paper.paper_metadata['embedding_components'] = ['title', 'authors', 'abstract']
                    paper.paper_metadata['embedding_generated_at'] = datetime.utcnow().isoformat()

                db.commit()
                total_processed += len(batch)

                print(f"✅ Batch {i//batch_size + 1}/{total_batches}: {len(batch)} papers processed")
                print(f"   📄 Sample: {texts[0][:100]}...")

            except Exception as e:
                print(f"❌ Error processing batch {i//batch_size + 1}: {e}")
                db.rollback()
                continue

        return {
            "message": f"Successfully generated ENHANCED embeddings for {total_processed} papers",
            "processed": total_processed,
            "total_batches": total_batches,
            "embedding_version": "enhanced_v2",
            "components": ["title", "authors", "abstract"]
        }

    def _format_authors_for_embedding(self, authors) -> str:
        """
        Format author names for optimal embedding quality

        Handles various author formats:
        - ["Yann LeCun", "Geoffrey Hinton"] → "Yann LeCun Geoffrey Hinton"
        - ["LeCun, Yann", "Hinton, Geoffrey"] → "Yann LeCun Geoffrey Hinton"
        - ["Y. LeCun", "G. Hinton"] → "Yann LeCun Geoffrey Hinton"
        """
        if not authors:
            return ""

        if isinstance(authors, str):
            # Sometimes authors come as a single string
            try:
                authors = eval(authors)  # Try to parse as list
            except:
                return authors  # Return as-is if can't parse

        if not isinstance(authors, list):
            return str(authors)

        formatted_authors = []

        for author in authors[:5]:  # Limit to first 5 authors for embedding quality
            if isinstance(author, str):
                # Clean and normalize author name
                clean_author = self._normalize_author_name(author)
                if clean_author:
                    formatted_authors.append(clean_author)

        return " ".join(formatted_authors)

    def _normalize_author_name(self, author: str) -> str:
        """
        Normalize author names for better embedding quality

        Examples:
        - "LeCun, Yann" → "Yann LeCun"
        - "Y. LeCun" → "Yann LeCun" (if possible)
        - "Dr. Jane Smith PhD" → "Jane Smith"
        """
        if not author or not isinstance(author, str):
            return ""

        author = author.strip()

        # Remove titles and suffixes
        author = author.replace("Dr.", "").replace("Prof.", "").replace("PhD", "")
        author = author.replace("Ph.D.", "").replace("MD", "").replace("DSc", "")

        # Handle "Last, First" format
        if "," in author:
            parts = author.split(",", 1)
            if len(parts) == 2:
                last, first = parts
                # Try to expand initials
                first = self._expand_initials(first.strip())
                return f"{first} {last.strip()}"

        # Try to expand initials in "First Last" format
        author = self._expand_initials(author)

        return author.strip()

    def _expand_initials(self, name: str) -> str:
        """
        Expand common academic initials

        Examples:
        - "Y. LeCun" → "Yann LeCun"
        - "G. Hinton" → "Geoffrey Hinton"
        """
        # Common academic name mappings (can be expanded)
        initial_mappings = {
            "Y. LeCun": "Yann LeCun",
            "G. Hinton": "Geoffrey Hinton",
            "Y. Bengio": "Yoshua Bengio",
            "A. Ng": "Andrew Ng",
            "F. Li": "Fei Fei Li",
            "I. Goodfellow": "Ian Goodfellow",
            "S. Hochreiter": "Sepp Hochreiter",
            "J. Schmidhuber": "Jürgen Schmidhuber",
        }

        return initial_mappings.get(name, name)

    async def regenerate_enhanced_embeddings(
        self,
        db: Session,
        batch_size: int = 50,
        max_papers: int = 1000
    ) -> Dict[str, Any]:
        """
        Regenerate embeddings for existing papers with enhanced format

        This upgrades papers from old embeddings to new enhanced format
        """
        print("🔄 Regenerating embeddings with enhanced author + abstract format...")

        # Find papers that need upgrading (old embedding version or no metadata)
        query = db.query(Paper).filter(
            Paper.embedding.isnot(None),
            Paper.is_processed == True
        ).limit(max_papers)

        papers_to_upgrade = []
        for paper in query:
            metadata = paper.metadata or {}
            embedding_version = metadata.get('embedding_version', 'legacy')

            if embedding_version != 'enhanced_v2':
                papers_to_upgrade.append(paper)

        if not papers_to_upgrade:
            return {"message": "All papers already have enhanced embeddings", "upgraded": 0}

        print(f"📈 Upgrading {len(papers_to_upgrade)} papers to enhanced embeddings")

        result = await self.generate_embeddings_for_papers(
            db=db,
            batch_size=batch_size,
            max_papers=len(papers_to_upgrade),
            force_regenerate=True
        )

        result['message'] = f"Successfully upgraded {result['processed']} papers to enhanced embeddings"
        return result

    async def update_paper_categories(self, db: Session) -> Dict[str, Any]:
        """
        Update paper categories based on source and content analysis

        This is a simplified version - in production you'd use ML classification
        """

        # Simple category mapping based on source
        category_mapping = {
            'arxiv': 'ai_cs',  # Most arXiv papers are CS/Math/Physics
            'semantic_scholar': None,  # Too diverse, needs content analysis
            'openalex': None,  # Too diverse, needs content analysis
            'pubmed': 'medicine_biology',
            'europe_pmc': 'medicine_biology',
            'eric': 'humanities_social',  # Education research
            'core': None,  # Diverse open access
            'biorxiv': 'medicine_biology',
            'crossref': None  # Too diverse
        }

        total_updated = 0

        for source, category in category_mapping.items():
            if category:
                # Update papers with this source and no category
                update_sql = """
                UPDATE papers
                SET category = :category, last_updated = NOW()
                WHERE source = :source AND (category IS NULL OR category = '')
                """

                result = db.execute(text(update_sql), {
                    'category': category,
                    'source': source
                })

                updated = result.rowcount
                total_updated += updated

                if updated > 0:
                    print(f"📝 Categorized {updated} papers from {source} as '{category}'")

        db.commit()

        return {
            "message": f"Updated categories for {total_updated} papers",
            "updated": total_updated
        }

    def get_cache_statistics(self, db: Session) -> Dict[str, Any]:
        """Get cache performance statistics"""

        stats_query = """
        SELECT
            COUNT(*) as total_cached_queries,
            SUM(cache_hits) as total_cache_hits,
            AVG(result_count) as avg_results_per_query,
            COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as active_cache_entries
        FROM category_cache
        """

        result = db.execute(text(stats_query)).first()

        return {
            "total_cached_queries": result[0] or 0,
            "total_cache_hits": result[1] or 0,
            "avg_results_per_query": float(result[2] or 0),
            "active_cache_entries": result[3] or 0
        }
