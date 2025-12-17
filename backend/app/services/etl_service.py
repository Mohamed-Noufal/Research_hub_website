"""
ETL (Extract, Transform, Load) Service for Academic Search Platform
Handles automated data collection, processing, and indexing.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.unified_search_service import UnifiedSearchService
from app.services.enhanced_vector_service import EnhancedVectorService
from app.services.search_service import UnifiedSearchService
from app.utils.cache import CacheService

class ETLService:
    """ETL service for data collection and processing"""

    def __init__(
        self,
        search_service: UnifiedSearchService,
        vector_service: EnhancedVectorService,
        cache_service: CacheService
    ):
        self.search_service = search_service
        self.vector_service = vector_service
        self.cache_service = cache_service

    async def run_full_etl_pipeline(self, db: Session) -> Dict[str, Any]:
        """Run complete ETL pipeline"""

        print("🚀 Starting full ETL pipeline...")

        start_time = datetime.utcnow()
        results = {
            "pipeline_start": start_time.isoformat(),
            "stages": {},
            "overall_success": False,
            "total_processed": 0
        }

        try:
            # Stage 1: Collect new papers from all sources
            print("\n📥 Stage 1: Collecting new papers...")
            collection_result = await self._collect_new_papers(db)
            results["stages"]["collection"] = collection_result

            # Stage 2: Generate embeddings for new papers
            print("\n🧠 Stage 2: Generating embeddings...")
            embedding_result = await self.vector_service.generate_embeddings_for_papers(
                db=db, batch_size=50, max_papers=1000  # Process in smaller batches
            )
            results["stages"]["embeddings"] = embedding_result

            # Stage 3: Update paper categories
            print("\n🏷️ Stage 3: Updating paper categories...")
            category_result = await self.vector_service.update_paper_categories(db)
            results["stages"]["categories"] = category_result

            # Stage 4: Refresh category caches
            print("\n🗄️ Stage 4: Refreshing category caches...")
            cache_result = await self._refresh_category_caches(db)
            results["stages"]["cache_refresh"] = cache_result

            # Stage 5: Update source metadata
            print("\n📊 Stage 5: Updating source metadata...")
            metadata_result = await self._update_source_metadata(db)
            results["stages"]["metadata"] = metadata_result

            # Calculate totals
            total_processed = (
                collection_result.get("total_collected", 0) +
                embedding_result.get("processed", 0) +
                category_result.get("updated", 0)
            )

            results["total_processed"] = total_processed
            results["overall_success"] = True
            results["pipeline_duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()

            print(f"\n✅ ETL Pipeline completed successfully!")
            print(f"   📊 Total processed: {total_processed} items")
            print(f"   ⏱️ Duration: {results['pipeline_duration_seconds']:.2f} seconds")
        except Exception as e:
            results["error"] = str(e)
            results["overall_success"] = False
            print(f"\n❌ ETL Pipeline failed: {e}")

        # Log ETL job completion
        await self._log_etl_job(db, "full_pipeline", results)

        return results

    async def _collect_new_papers(self, db: Session) -> Dict[str, Any]:
        """Collect new papers from all sources"""

        # Define collection queries for each source
        collection_queries = {
            'arxiv': [
                'machine learning', 'artificial intelligence', 'computer vision',
                'natural language processing', 'deep learning', 'neural networks'
            ],
            'pubmed': [
                'clinical trials', 'medical research', 'drug development',
                'genomics', 'biotechnology', 'public health'
            ],
            'eric': [
                'education technology', 'learning science', 'pedagogy',
                'educational research', 'teaching methods', 'curriculum development'
            ],
            'semantic_scholar': [
                'machine learning', 'artificial intelligence', 'data science'
            ],
            'openalex': [
                'interdisciplinary research', 'scientific collaboration'
            ],
            'europe_pmc': [
                'biomedical research', 'clinical studies', 'molecular biology'
            ]
        }

        total_collected = 0
        sources_processed = 0

        for source, queries in collection_queries.items():
            source_total = 0

            for query in queries:
                try:
                    # Search and store results
                    results = await self.search_service.search(
                        query=query,
                        limit=50,  # Collect more papers per query
                        sources=[source],
                        use_cache=False
                    )

                    # Store papers (this will be handled by existing save_papers_to_db)
                    if results.get('papers'):
                        await self.search_service.save_papers_to_db(results['papers'], db)
                        source_total += len(results['papers'])

                except Exception as e:
                    print(f"   ⚠️ Error collecting from {source} for '{query}': {e}")
                    continue

            if source_total > 0:
                print(f"   ✅ {source}: {source_total} papers collected")
                total_collected += source_total
                sources_processed += 1

        return {
            "total_collected": total_collected,
            "sources_processed": sources_processed,
            "collection_queries": len(collection_queries)
        }

    async def _refresh_category_caches(self, db: Session) -> Dict[str, Any]:
        """Refresh category caches with popular queries"""

        # Define popular queries for each category
        popular_queries = {
            'ai_cs': [
                'machine learning', 'deep learning', 'artificial intelligence',
                'computer vision', 'natural language processing'
            ],
            'medicine_biology': [
                'clinical trials', 'drug development', 'genomics',
                'cancer research', 'molecular biology'
            ],
            'humanities_social': [
                'educational research', 'learning science', 'pedagogy',
                'curriculum development', 'teaching methods'
            ],
            'agriculture_animal': [
                'agricultural technology', 'animal science', 'farming',
                'crop science', 'livestock management'
            ],
            'economics_business': [
                'economic development', 'business strategy', 'finance',
                'market analysis', 'entrepreneurship'
            ]
        }

        total_cached = 0
        categories_processed = 0

        for category, queries in popular_queries.items():
            category_cached = 0

            for query in queries:
                try:
                    # Perform search and cache results
                    results = await self.vector_service.category_search_with_cache(
                        db=db,
                        query=query,
                        category=category,
                        limit=25,  # Smaller limit for cache
                        cache_ttl_hours=48  # Longer cache for popular queries
                    )

                    if not results.get('cached', False):  # Only count if newly cached
                        category_cached += 1

                except Exception as e:
                    print(f"   ⚠️ Error caching {category} query '{query}': {e}")
                    continue

            if category_cached > 0:
                print(f"   ✅ {category}: {category_cached} queries cached")
                total_cached += category_cached
                categories_processed += 1

        return {
            "total_cached": total_cached,
            "categories_processed": categories_processed
        }

    async def _update_source_metadata(self, db: Session) -> Dict[str, Any]:
        """Update source metadata with current statistics"""

        sources = [
            'arxiv', 'semantic_scholar', 'openalex', 'crossref',
            'pubmed', 'europe_pmc', 'eric', 'core', 'biorxiv'
        ]

        total_updated = 0

        for source in sources:
            try:
                # Get current paper count for source
                count_query = """
                SELECT COUNT(*) as paper_count
                FROM papers
                WHERE source = :source
                """

                result = db.execute(text(count_query), {'source': source}).first()
                paper_count = result[0] if result else 0

                # Update source metadata
                update_query = """
                UPDATE source_metadata
                SET total_papers = :paper_count,
                    last_fetched = NOW()
                WHERE source_name = :source
                """

                db.execute(text(update_query), {
                    'paper_count': paper_count,
                    'source': source
                })

                total_updated += 1

            except Exception as e:
                print(f"   ⚠️ Error updating metadata for {source}: {e}")
                continue

        db.commit()

        return {
            "sources_updated": total_updated,
            "total_sources": len(sources)
        }

    async def _log_etl_job(
        self,
        db: Session,
        job_type: str,
        results: Dict[str, Any]
    ):
        """Log ETL job completion"""

        try:
            insert_sql = """
            INSERT INTO etl_jobs (
                job_type, status, started_at, completed_at,
                records_processed, errors
            ) VALUES (
                :job_type,
                CASE WHEN :success THEN 'completed' ELSE 'failed' END,
                :started_at,
                NOW(),
                :records_processed,
                :errors
            )
            """

            db.execute(text(insert_sql), {
                'job_type': job_type,
                'success': results.get('overall_success', False),
                'started_at': results.get('pipeline_start'),
                'records_processed': results.get('total_processed', 0),
                'errors': results.get('error')
            })

            db.commit()

        except Exception as e:
            print(f"⚠️ Failed to log ETL job: {e}")

    async def get_etl_statistics(self, db: Session) -> Dict[str, Any]:
        """Get ETL pipeline statistics"""

        stats_query = """
        SELECT
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_jobs,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
            SUM(records_processed) as total_records_processed,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_job_duration_seconds,
            MAX(completed_at) as last_job_completion
        FROM etl_jobs
        WHERE started_at >= NOW() - INTERVAL '30 days'
        """

        try:
            result = db.execute(text(stats_query)).first()

            return {
                "total_jobs_last_30_days": result[0] or 0,
                "successful_jobs": result[1] or 0,
                "failed_jobs": result[2] or 0,
                "total_records_processed": result[3] or 0,
                "avg_job_duration_seconds": float(result[4] or 0),
                "last_job_completion": result[5].isoformat() if result[5] else None
            }

        except Exception as e:
            print(f"Error getting ETL statistics: {e}")
            return {}

    async def cleanup_old_cache_entries(self, db: Session, days_old: int = 7) -> Dict[str, Any]:
        """Clean up old cache entries"""

        try:
            # Delete expired cache entries
            delete_expired_sql = """
            DELETE FROM category_cache
            WHERE expires_at < NOW()
            """

            expired_result = db.execute(text(delete_expired_sql))
            expired_deleted = expired_result.rowcount

            # Delete very old cache entries (regardless of expiry)
            delete_old_sql = f"""
            DELETE FROM category_cache
            WHERE last_updated < NOW() - INTERVAL '{days_old} days'
            """

            old_result = db.execute(text(delete_old_sql))
            old_deleted = old_result.rowcount

            db.commit()

            return {
                "expired_entries_deleted": expired_deleted,
                "old_entries_deleted": old_deleted,
                "total_cleaned": expired_deleted + old_deleted
            }

        except Exception as e:
            print(f"Error cleaning cache: {e}")
            db.rollback()
            return {"error": str(e)}
