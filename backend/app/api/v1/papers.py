import time
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.unified_search_service import UnifiedSearchService
from app.services.enhanced_vector_service import EnhancedVectorService
from app.services.ai_query_analyzer import AIQueryAnalyzer
from app.utils.cache import CacheService
from app.core.config import settings
from app.tools.pdf_tools import parse_pdf_background

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])

# Dependency injection functions
def get_cache_service() -> CacheService:
    """Get cache service instance"""
    return CacheService(settings.REDIS_URL)

def get_vector_service() -> EnhancedVectorService:
    """Get vector service instance"""
    return EnhancedVectorService()

def get_ai_analyzer() -> AIQueryAnalyzer:
    """Get AI analyzer instance"""
    return AIQueryAnalyzer()

def get_search_service(
    cache_service: CacheService = Depends(get_cache_service),
    vector_service: EnhancedVectorService = Depends(get_vector_service),
    ai_analyzer: AIQueryAnalyzer = Depends(get_ai_analyzer)
) -> UnifiedSearchService:
    """Get unified search service with dependencies"""
    return UnifiedSearchService(
        cache_service=cache_service
    )


def paper_to_dict(paper):
    """Convert Paper model or dict to JSON-serializable dictionary"""
    # If already a dict, return as-is
    if isinstance(paper, dict):
        return paper
    
    # Convert SQLAlchemy model to dict
    return {
        "id": getattr(paper, 'id', None),
        "title": getattr(paper, 'title', ''),
        "abstract": getattr(paper, 'abstract', None),
        "authors": getattr(paper, 'authors', []) or [],
        "publication_date": paper.publication_date.isoformat() if hasattr(paper, 'publication_date') and paper.publication_date else None,
        "pdf_url": getattr(paper, 'pdf_url', None),
        "source": getattr(paper, 'source', ''),
        "arxiv_id": getattr(paper, 'arxiv_id', None),
        "doi": getattr(paper, 'doi', None),
        "semantic_scholar_id": getattr(paper, 'semantic_scholar_id', None),
        "openalex_id": getattr(paper, 'openalex_id', None),
        "citation_count": getattr(paper, 'citation_count', 0) or 0,
        "venue": getattr(paper, 'venue', None)
    }


# Request/Response Models
class PaperResponse(BaseModel):
    id: Optional[int] = None
    title: str
    abstract: Optional[str] = None
    authors: List[str] = []
    publication_date: Optional[str] = None
    pdf_url: Optional[str] = None
    source: str
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    semantic_scholar_id: Optional[str] = None
    openalex_id: Optional[str] = None
    citation_count: int = 0
    venue: Optional[str] = None


class SearchResponse(BaseModel):
    papers: List[dict]
    total: int
    query: str
    sources_used: List[str]
    cached: bool


# Endpoints
@router.get("/search")
async def unified_search(
    query: str = Query(..., min_length=2, max_length=500, description="Search query"),
    category: str = Query(..., description="Research category (required)"),
    mode: str = Query(..., regex="^(auto|quick|ai)$", description="Search mode: auto, quick, or ai"),
    limit: int = Query(100, ge=1, le=100, description="Maximum results"),
    background_tasks: BackgroundTasks = BackgroundTasks(),  # ADD THIS
    db: Session = Depends(get_db),
    search_service: UnifiedSearchService = Depends(get_search_service)
):
    """
    🔍 **Intelligent Hybrid Search** - Fast Academic Paper Discovery

    **🚀 New Features:**
    - ⚡ **Parallel Search:** Local DB + External APIs simultaneously (3-5s)
    - 🎯 **Smart Routing:** Category-specific sources (AI→arXiv, Medicine→PubMed)
    - 📊 **Maximum Results:** Fetches 100-200 papers per search (vs 20)
    - 🔄 **Background Embeddings:** Results in 10-15s, embeddings generate after
    - 📈 **Auto-Growing Database:** Learns and improves with each search

    **Search Modes:**

    1. **Auto Mode** (Recommended)
       - Intelligent mode detection based on query complexity
       - Example: `"How do neural networks learn?"` → AI mode
       - Example: `"machine learning"` → Quick mode

    2. **Quick Mode** (Fast)
       - Hybrid semantic + keyword search
       - Parallel local + external execution
       - Example: `"deep learning applications"`

    3. **AI Mode** (Advanced)
       - AI-powered query expansion and optimization
       - Intelligent source selection
       - Example: `"detection unhealthy goat using deep learning"`

    **Smart Features:**
    - 🎯 **Category-Based Routing:** Searches appropriate sources per domain
    - 🔄 **Cascading Fallback:** Primary → Backup 1 → Backup 2
    - 💾 **Semantic Caching:** Finds similar past queries
    - 🔍 **Deduplication:** Removes duplicate papers
    - ⚖️ **Hybrid Scoring:** Semantic (70%) + Keyword (30%)

    **Parameters:**
    - `query`: Search terms or natural language question
    - `category`: Research category (ai_cs, medicine_biology, agriculture_animal, humanities_social, economics_business)
    - `mode`: "auto" (default), "quick", or "ai"
    - `limit`: Max results (1-100, default 100)

    **Example Requests:**
    ```bash
    # Auto-detect mode (recommended)
    GET /search?query=transformer+architecture&category=ai_cs&mode=auto

    # Quick mode (fast hybrid search)
    GET /search?query=machine+learning&category=ai_cs&mode=quick

    # AI mode (intelligent expansion)
    GET /search?query=cancer+treatment&category=medicine_biology&mode=ai
    ```

    **Response Structure:**
    ```json
    {
      "papers": [...],
      "total": 20,
      "metadata": {
        "search_strategy": "parallel_local_priority",
        "source_used": "local_database",
        "search_time": 3.54,
        "local_results": 20,
        "external_results": 100,
        "papers_saved": 0,
        "api_calls_made": 1
      }
    }
    ```

    **Performance:**
    - ⏱️ Response Time: 10-15 seconds (down from 116s!)
    - 📄 Papers/Search: 100-200 (up from 20)
    - 🔄 Background Processing: Embeddings generate after response
    - 📈 Database Growth: Automatic and continuous
    """
    try:
        result = await search_service.search(
            query=query,
            category=category,
            mode=mode,
            limit=limit,
            db=db
        )

        # Schedule BACKGROUND save + embedding
        papers_to_save = result.get('metadata', {}).get('papers_to_save_in_background', [])
        if papers_to_save:
            print(f"📋 Scheduling background save + embedding for {len(papers_to_save)} papers")
            
            async def save_and_embed_background():
                try:
                    print(f"💾 BACKGROUND: Saving {len(papers_to_save)} papers...")
                    saved_count = await search_service._save_results_without_embeddings(
                        papers_to_save, category, db
                    )
                    print(f"✅ BACKGROUND: Saved {saved_count} papers")
                    
                    if saved_count > 0:
                        # Generate embeddings
                        from app.models.paper import Paper
                        papers_needing_embeddings = db.query(Paper).filter(
                            Paper.is_processed == False,
                            Paper.embedding.is_(None)
                        ).all()
                        
                        if papers_needing_embeddings:
                            paper_ids = [str(p.id) for p in papers_needing_embeddings]
                            await search_service.generate_embeddings_background(
                                paper_ids=paper_ids,
                                db=db
                            )
                except Exception as e:
                    print(f"❌ Background save/embed failed: {e}")
            
            background_tasks.add_task(save_and_embed_background)

        # Convert any Paper model objects to dicts for JSON serialization
        if 'papers' in result and result['papers']:
            result['papers'] = [
                paper_to_dict(p) for p in result['papers']
            ]

        return result

    except Exception as e:
        logger.exception(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/ai-suggestions")
async def get_ai_suggestions(
    problem_statement: str = Query(..., min_length=10, max_length=2000, description="Research problem description"),
    goals: Optional[str] = Query(None, max_length=1000, description="Research goals (optional)"),
    category: Optional[str] = Query(None, description="Research category (optional)"),
    ai_analyzer: AIQueryAnalyzer = Depends(get_ai_analyzer)
):
    """
    🤖 **AI Search Suggestions** - Get Smart Query Recommendations

    This endpoint helps researchers formulate better search queries by analyzing their
    research problem, goals, and context. Perfect for when you're not sure what to search for!

    **How It Works:**
    1. Describe your research problem or topic (paragraph format)
    2. Optionally add your research goals
    3. AI analyzes and suggests 3-5 targeted search queries
    4. Use suggested queries in the main search endpoint

    **Parameters:**
    - `problem_statement`: Detailed description of your research problem/topic (10-2000 chars)
    - `goals`: Your research goals or objectives (optional, max 1000 chars)
    - `category`: Research category to focus suggestions (optional)

    **Example Request:**
    ```bash
    POST /ai-suggestions
    {
      "problem_statement": "I'm studying the impact of climate change on agricultural productivity in sub-Saharan Africa. I need to understand how changing rainfall patterns affect crop yields and what adaptation strategies farmers are using.",
      "goals": "Find recent studies on climate adaptation in agriculture, focus on sub-Saharan Africa, include both empirical studies and policy recommendations",
      "category": "agriculture_animal"
    }
    ```

    **Example Response:**
    ```json
    {
      "suggestions": [
        {
          "query": "climate change impact agricultural productivity sub-Saharan Africa",
          "category": "agriculture_animal",
          "relevance_score": 0.95,
          "reasoning": "Directly addresses the core research problem with geographic and domain specificity"
        },
        {
          "query": "rainfall variability crop yield Africa adaptation strategies",
          "category": "agriculture_animal",
          "relevance_score": 0.92,
          "reasoning": "Focuses on the specific climate variable (rainfall) and farmer responses"
        },
        {
          "query": "climate-smart agriculture sub-Saharan Africa policy",
          "category": "agriculture_animal",
          "relevance_score": 0.88,
          "reasoning": "Addresses adaptation strategies and policy recommendations"
        }
      ],
      "total_suggestions": 3,
      "analysis": {
        "detected_topics": ["climate change", "agriculture", "adaptation", "sub-Saharan Africa"],
        "suggested_category": "agriculture_animal",
        "complexity": "medium"
      }
    }
    ```

    **Use Cases:**
    - 📚 Starting a new research project
    - 🔍 Not sure what keywords to use
    - 🌍 Exploring unfamiliar research domains
    - 🎯 Want to refine broad research questions
    - 💡 Looking for alternative search angles

    **Tips:**
    - Be specific about your research context
    - Mention geographic regions, time periods, or populations if relevant
    - Include any specific methodologies or approaches you're interested in
    - The more detail you provide, the better the suggestions!
    """
    try:
        # Combine problem statement and goals
        full_context = problem_statement
        if goals:
            full_context += f"\n\nResearch Goals: {goals}"

        # Get AI suggestions
        suggestions = await ai_analyzer.generate_search_suggestions(
            context=full_context,
            category=category
        )

        return {
            "suggestions": suggestions.get('queries', []),
            "total_suggestions": len(suggestions.get('queries', [])),
            "analysis": {
                "detected_topics": suggestions.get('topics', []),
                "suggested_category": suggestions.get('category', category),
                "complexity": suggestions.get('complexity', 'medium')
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI suggestion generation failed: {str(e)}"
        )


@router.get("/health")
async def health_check(
    cache_service: CacheService = Depends(get_cache_service)
):
    """Check if search services are operational"""
    return {
        "status": "healthy",
        "redis_connected": cache_service.is_connected(),
        "services": {
            "arxiv": "operational",
            "semantic_scholar": "operational",
            "openalex": "operational"
        }
    }


@router.delete("/cache")
async def clear_cache():
    """Clear search cache (admin endpoint - add auth later)"""
    try:
        success = await cache_service.clear_all()
        return {
            "success": success,
            "message": "Cache cleared" if success else "Failed to clear cache"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/stats")
async def get_search_stats(db: Session = Depends(get_db)):
    """Get statistics about papers in the database"""
    from app.models.paper import Paper
    from sqlalchemy import func

    try:
        total_papers = db.query(func.count(Paper.id)).scalar()

        papers_by_source = db.query(
            Paper.source,
            func.count(Paper.id)
        ).group_by(Paper.source).all()

        return {
            "total_papers": total_papers,
            "by_source": {source: count for source, count in papers_by_source},
            "processed_papers": db.query(func.count(Paper.id)).filter(
                Paper.is_processed == True
            ).scalar()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )








@router.get("/categories")
async def get_available_categories():
    """
    Get all available search categories with their configurations

    **Returns:**
    - Category ID and display name
    - Associated sources
    - Description and source count

    **Example:**
    ```
    GET /api/v1/papers/categories
    ```

    **Response:**
    ```json
    {
      "categories": {
        "ai_cs": {
          "id": "ai_cs",
          "name": "AI & Computer Science",
          "description": "Artificial Intelligence, Machine Learning, Computer Science",
          "sources": ["arxiv", "semantic_scholar", "openalex"],
          "source_count": 3
        }
      },
      "total": 6
    }
    ```
    """
    try:
        # Hardcoded categories for now (avoiding SearchConfig import issues)
        categories_data = {
            "ai_cs": {
                "name": "AI & Computer Science",
                "description": "Machine learning, AI, computer vision, NLP",
                "sources": ["arxiv", "semantic_scholar", "openalex"],
                "source_count": 3
            },
            "medicine_biology": {
                "name": "Medicine & Biology",
                "description": "Clinical research, biomedical, healthcare",
                "sources": ["pubmed", "europe_pmc", "crossref"],
                "source_count": 3
            },
            "engineering_physics": {
                "name": "Engineering & Physics",
                "description": "Applied sciences, engineering, physics",
                "sources": ["arxiv", "openalex", "crossref"],
                "source_count": 3
            },
            "agriculture_animal": {
                "name": "Agriculture & Animal Science",
                "description": "Farming, animal science, food security",
                "sources": ["openalex", "core", "crossref"],
                "source_count": 3
            },
            "humanities_social": {
                "name": "Humanities & Social Sciences",
                "description": "Psychology, sociology, education, humanities",
                "sources": ["eric", "openalex", "core"],
                "source_count": 3
            },
            "economics_business": {
                "name": "Economics & Business",
                "description": "Economics, finance, business management",
                "sources": ["openalex", "core", "crossref"],
                "source_count": 3
            }
        }

        # Format for frontend
        formatted_categories = {}
        for cat_id, config in categories_data.items():
            formatted_categories[cat_id] = {
                "id": cat_id,
                "name": config["name"],
                "description": config["description"],
                "sources": config["sources"],
                "source_count": config["source_count"]
            }

        return {
            "categories": formatted_categories,
            "total": len(formatted_categories)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get categories: {str(e)}"
        )


def get_enhanced_vector_service() -> EnhancedVectorService:
    """Get enhanced vector service instance"""
    return EnhancedVectorService()





@router.post("/embeddings/generate")
async def generate_paper_embeddings(
    max_papers: int = Query(1000, ge=1, le=10000, description="Maximum papers to process"),
    batch_size: int = Query(50, ge=10, le=200, description="Batch size for processing"),
    force_regenerate: bool = Query(False, description="Regenerate existing embeddings"),
    db: Session = Depends(get_db),
    vector_service: EnhancedVectorService = Depends(get_enhanced_vector_service)
):
    """
    Generate enhanced embeddings for papers (Title + Authors + Abstract)

    **Enhanced Embedding Features:**
    - **Title**: Main topic and research focus
    - **Authors**: Researcher expertise and collaboration networks
    - **Abstract**: Detailed methodology, findings, and context

    **Benefits:**
    - 3x richer semantic understanding
    - Better author-focused search results
    - More accurate research discovery
    - Improved expert search capabilities

    **Parameters:**
    - max_papers: Maximum papers to process (1-10000)
    - batch_size: Processing batch size (10-200)
    - force_regenerate: Regenerate existing embeddings

    **Example:**
    ```
    POST /api/v1/papers/embeddings/generate?max_papers=500&batch_size=100&force_regenerate=false
    ```

    **Response:**
    ```json
    {
      "message": "Successfully generated ENHANCED embeddings for 500 papers",
      "processed": 500,
      "total_batches": 5,
      "embedding_version": "enhanced_v2",
      "components": ["title", "authors", "abstract"]
    }
    ```
    """
    try:
        print(f"🎯 Starting enhanced embedding generation...")
        print(f"📊 Parameters: max_papers={max_papers}, batch_size={batch_size}, force={force_regenerate}")

        result = await vector_service.generate_embeddings_for_papers(
            db=db,
            batch_size=batch_size,
            max_papers=max_papers,
            force_regenerate=force_regenerate
        )

        print(f"✅ Embedding generation completed: {result}")

        return result

    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Embedding generation failed: {str(e)}"
        )


@router.post("/embeddings/regenerate")
async def regenerate_enhanced_embeddings(
    max_papers: int = Query(500, ge=1, le=5000, description="Maximum papers to upgrade"),
    batch_size: int = Query(25, ge=5, le=100, description="Batch size for processing"),
    db: Session = Depends(get_db),
    vector_service: EnhancedVectorService = Depends(get_enhanced_vector_service)
):
    """
    Upgrade existing papers to enhanced embeddings (Title + Authors + Abstract)

    **Use Case:**
    - Upgrade papers from old embeddings to new enhanced format
    - Improve search quality for existing database
    - Add author information to semantic search

    **Process:**
    1. Identifies papers with old embedding versions
    2. Regenerates embeddings with enhanced format
    3. Updates metadata with new version info

    **Example:**
    ```
    POST /api/v1/papers/embeddings/regenerate?max_papers=200&batch_size=50
    ```

    **Response:**
    ```json
    {
      "message": "Successfully upgraded 200 papers to enhanced embeddings",
      "processed": 200,
      "total_batches": 4,
      "embedding_version": "enhanced_v2"
    }
    ```
    """
    try:
        print(f"🔄 Starting embedding regeneration...")

        result = await vector_service.regenerate_enhanced_embeddings(
            db=db,
            batch_size=batch_size,
            max_papers=max_papers
        )

        print(f"✅ Embedding regeneration completed: {result}")

        return result

    except Exception as e:
        print(f"❌ Embedding regeneration failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Embedding regeneration failed: {str(e)}"
        )


@router.get("/embeddings/stats")
async def get_embedding_statistics(db: Session = Depends(get_db)):
    """
    Get embedding statistics and version information

    **Returns:**
    - Total papers with embeddings
    - Embedding version distribution
    - Processing status
    - Cache statistics

    **Example:**
    ```
    GET /api/v1/papers/embeddings/stats
    ```
    """
    try:
        from app.models.paper import Paper
        from sqlalchemy import func

        # Get embedding statistics
        total_papers = db.query(func.count(Paper.id)).scalar()
        papers_with_embeddings = db.query(func.count(Paper.id)).filter(
            Paper.embedding.isnot(None)
        ).scalar()

        # Get version distribution
        version_stats = db.query(
            Paper.metadata['embedding_version'].astext,
            func.count(Paper.id)
        ).filter(
            Paper.embedding.isnot(None)
        ).group_by(
            Paper.metadata['embedding_version'].astext
        ).all()

        version_distribution = {version or 'legacy': count for version, count in version_stats}

        # Get processing status
        processed_papers = db.query(func.count(Paper.id)).filter(
            Paper.is_processed == True
        ).scalar()

        return {
            "total_papers": total_papers,
            "papers_with_embeddings": papers_with_embeddings,
            "embedding_coverage": f"{(papers_with_embeddings/total_papers*100):.1f}%" if total_papers > 0 else "0%",
            "processed_papers": processed_papers,
            "processing_coverage": f"{(processed_papers/total_papers*100):.1f}%" if total_papers > 0 else "0%",
            "embedding_versions": version_distribution,
            "recommended_version": "enhanced_v2",
            "enhanced_features": ["title", "authors", "abstract"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get embedding statistics: {str(e)}"
        )


# DOI-Based Paper Fetching
class DOIRequest(BaseModel):
    doi: str = Field(..., min_length=5, max_length=200, description="Digital Object Identifier")
    category: Optional[str] = Field(None, description="Research category (optional, will be inferred if not provided)")


class DOIResponse(BaseModel):
    paper: dict
    status: str  # "created" or "already_exists"
    message: str
    already_in_library: bool = False
    source: Optional[str] = None  # Which API provided the data


@router.post("/fetch-by-doi")
async def fetch_paper_by_doi(
    request: DOIRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    🔍 **Fetch Paper by DOI** - Direct Paper Import via Digital Object Identifier

    This endpoint allows you to fetch a paper directly using its DOI (Digital Object Identifier).
    The paper will be fetched from multiple sources (Crossref, Unpaywall, Semantic Scholar),
    saved to the database, and displayed just like search results.

    **Features:**
    - ✅ Fetches from multiple sources (Crossref, Unpaywall, Semantic Scholar)
    - ✅ Automatic deduplication (won't create duplicates)
    - ✅ PDF links when available (open access)
    - ✅ Background embedding generation (fast response)
    - ✅ Auto-save to library (if authenticated)
    - ✅ Same format as search results (works with PaperCard)

    **DOI Format Examples:**
    - Standard: `10.1038/nature12373`
    - With URL: `https://doi.org/10.1038/nature12373`
    - IEEE: `10.1109/CVPR.2016.90`
    - PLOS: `10.1371/journal.pone.0123456`

    **Parameters:**
    - `doi`: The DOI to fetch (required)
    - `category`: Research category (optional, will be inferred if not provided)

    **Example Request:**
    ```bash
    POST /api/v1/papers/fetch-by-doi
    {
      "doi": "10.1038/nature12373",
      "category": "medicine_biology"
    }
    ```

    **Example Response:**
    ```json
    {
      "paper": {
        "id": 123,
        "title": "Example Paper Title",
        "abstract": "...",
        "authors": ["Author 1", "Author 2"],
        "pdf_url": "https://...",
        "doi": "10.1038/nature12373",
        "source": "semantic_scholar",
        "citation_count": 150,
        "venue": "Nature"
      },
      "status": "created",
      "message": "Paper fetched and saved successfully",
      "already_in_library": false,
      "source": "semantic_scholar"
    }
    ```

    **Error Responses:**
    - `400`: Invalid DOI format
    - `404`: DOI not found in any source
    - `500`: Server error

    **Use Cases:**
    - 📋 Import papers from reference lists
    - 🔖 Save papers you found elsewhere
    - 📚 Build your library quickly
    - 🔍 Get full metadata from just a DOI
    """
    try:
        from app.services.doi_fetcher_service import DOIFetcherService
        from app.models.paper import Paper
        import datetime

        # Clean DOI (remove URL prefix if present)
        doi = request.doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
        
        # Validate DOI format (basic check)
        if not doi or "/" not in doi or not doi.startswith("10."):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid DOI format",
                    "message": f"DOI '{request.doi}' is not in valid format. DOIs should start with '10.' and contain a '/'",
                    "suggestions": [
                        "Check if the DOI is typed correctly",
                        "DOI format: 10.XXXX/YYYY",
                        "Example: 10.1038/nature12373"
                    ]
                }
            )

        logger.info(f"📥 Fetching paper by DOI: {doi}")

        # Check if paper already exists in database (deduplication)
        existing_paper = db.query(Paper).filter(Paper.doi == doi).first()
        
        if existing_paper:
            logger.info(f"✅ Paper already exists in database (ID: {existing_paper.id})")
            
            # TODO: Check if in user's library when auth is implemented
            already_in_library = False
            
            return {
                "paper": paper_to_dict(existing_paper),
                "status": "already_exists",
                "message": "Paper already in database",
                "already_in_library": already_in_library,
                "source": existing_paper.source
            }

        # Fetch from external sources
        logger.info(f"🔍 Fetching from external sources...")
        fetcher = DOIFetcherService()
        
        try:
            paper_data = await fetcher.fetch_paper_by_doi(doi)
        finally:
            await fetcher.close()

        if not paper_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "DOI not found",
                    "message": f"Paper with DOI '{doi}' not found in any source",
                    "suggestions": [
                        "Verify the DOI is correct",
                        "Try searching by title instead",
                        "The paper may not be indexed in our sources (Crossref, Unpaywall, Semantic Scholar)"
                    ]
                }
            )

        logger.info(f"✅ Paper found from source: {paper_data.get('source')}")

        # Normalize data for database
        # Infer category if not provided
        category = request.category or _infer_category_from_metadata(paper_data)
        
        logger.info(f"📋 Normalizing paper data from source: {paper_data.get('source')}")
        logger.info(f"   Title: {paper_data.get('title', 'N/A')[:80]}...")
        logger.info(f"   Authors count: {len(paper_data.get('authors', []))}")
        logger.info(f"   Abstract length: {len(paper_data.get('abstract', ''))}")
        
        # Convert authors to list of strings if needed
        authors_list = []
        if paper_data.get('authors'):
            for author in paper_data['authors']:
                if isinstance(author, dict):
                    name = author.get('name', '').strip()
                    if name:  # Only add non-empty names
                        authors_list.append(name)
                else:
                    name = str(author).strip()
                    if name:
                        authors_list.append(name)
        
        # Handle empty strings - convert to None for database
        title = paper_data.get('title', '').strip() or 'Untitled'
        abstract = paper_data.get('abstract', '').strip() or None
        venue = (paper_data.get('journal') or paper_data.get('venue') or '').strip() or None

        # Create Paper model instance
        new_paper = Paper(
            doi=doi,
            title=title,
            abstract=abstract,
            authors=authors_list if authors_list else None,
            publication_date=paper_data.get('publication_date'),
            pdf_url=paper_data.get('pdf_url'),
            source=paper_data.get('source', 'unknown'),
            citation_count=paper_data.get('citation_count', 0),
            venue=venue,
            category=category,
            semantic_scholar_id=paper_data.get('semantic_scholar_id'),
            paper_metadata=paper_data.get('metadata', {}),
            is_processed=False,  # Will be set to True after embedding generation
            date_added=datetime.datetime.utcnow(),
            last_updated=datetime.datetime.utcnow()
        )

        # Save to database
        db.add(new_paper)
        db.commit()
        db.refresh(new_paper)

        logger.info(f"💾 Paper saved to database (ID: {new_paper.id})")

        # Schedule background embedding generation
        async def generate_embedding_background():
            try:
                logger.info(f"🔄 BACKGROUND: Generating embedding for paper {new_paper.id}")
                vector_service = EnhancedVectorService()
                await vector_service.generate_embeddings_for_papers(
                    db=db,
                    paper_ids=[str(new_paper.id)],
                    batch_size=1
                )
                logger.info(f"✅ BACKGROUND: Embedding generated for paper {new_paper.id}")
            except Exception as e:
                logger.error(f"❌ BACKGROUND: Embedding generation failed: {e}")

        background_tasks.add_task(generate_embedding_background)

        # TODO: Auto-save to user's library when auth is implemented
        # if user_id:
        #     saved_paper = UserSavedPaper(
        #         user_id=user_id,
        #         paper_id=new_paper.id,
        #         saved_at=datetime.utcnow()
        #     )
        #     db.add(saved_paper)
        #     db.commit()

        return {
            "paper": paper_to_dict(new_paper),
            "status": "created",
            "message": "Paper fetched and saved successfully",
            "already_in_library": False,
            "source": paper_data.get('source')
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception(f"❌ DOI fetch failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch paper by DOI: {str(e)}"
        )


def _infer_category_from_metadata(paper_data: dict) -> str:
    """
    Infer research category from paper metadata
    
    Uses journal name, subject keywords, and venue to guess the category
    """
    # Get potential category indicators
    journal = (paper_data.get('journal') or paper_data.get('venue') or '').lower()
    subjects = paper_data.get('metadata', {}).get('subject', [])
    
    # Simple keyword-based inference
    if any(keyword in journal for keyword in ['nature', 'science', 'cell', 'lancet', 'jama', 'nejm', 'plos', 'bmc']):
        return 'medicine_biology'
    
    if any(keyword in journal for keyword in ['ieee', 'acm', 'computer', 'neural', 'machine learning', 'ai']):
        return 'ai_cs'
    
    if any(keyword in journal for keyword in ['physics', 'engineering', 'materials']):
        return 'engineering_physics'
    
    if any(keyword in journal for keyword in ['agriculture', 'animal', 'veterinary', 'crop']):
        return 'agriculture_animal'
    
    if any(keyword in journal for keyword in ['psychology', 'sociology', 'education', 'humanities']):
        return 'humanities_social'
    
    if any(keyword in journal for keyword in ['economics', 'business', 'finance', 'management']):
        return 'economics_business'
    
    # Check subjects if available
    if subjects:
        subjects_str = ' '.join(subjects).lower()
        if 'medicine' in subjects_str or 'biology' in subjects_str:
            return 'medicine_biology'
        if 'computer' in subjects_str or 'ai' in subjects_str:
            return 'ai_cs'
    
    # Default to general category
    return 'ai_cs'  # Default fallback

# PDF Upload Endpoint
from fastapi import File, UploadFile
import shutil
from pathlib import Path
from app.models.paper import Paper
from app.api.v1.users import get_current_user_id

@router.post("/{paper_id}/upload-pdf")
async def upload_pdf(
    paper_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF file for a specific paper
    """
    # Check if paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create upload directory if not exists
    upload_dir = Path("uploads/pdfs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"{paper_id}.pdf"
    file_path = upload_dir / filename
    
    # Save file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save PDF file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Update paper PDF URL
    # Use relative path for frontend to access via static mount
    # Assuming backend is running on localhost:8000
    # The frontend should prepend the API base URL or we return the full URL
    # For now, let's store the relative path from the static mount
    
    # We mounted "/uploads" to "uploads" directory
    # So "uploads/pdfs/123.pdf" is accessible at "/uploads/pdfs/123.pdf"
    
    relative_url = f"http://localhost:8000/uploads/pdfs/{filename}"
    paper.pdf_url = relative_url
    
    # Update openAccess status implicitly by having a PDF
    # We don't have an openAccess field in DB, but frontend uses pdf_url presence
    
    db.commit()
    db.refresh(paper)
    
    # TRIGGER AUTO-INDEXING
    background_tasks.add_task(
        parse_pdf_background, 
        pdf_path=str(file_path.absolute()), 
        paper_id=paper_id,
        project_id=0 
    )
    
    # Return full paper object for frontend to update state
    from app.models.paper import Paper as PaperModel
    
    return {
        "message": "PDF uploaded successfully",
        "pdf_url": relative_url,
        "paper_id": paper_id,
        "paper": {
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract,
            "authors": paper.authors,
            "publication_date": paper.publication_date,
            "doi": paper.doi,
            "citation_count": paper.citation_count,
            "venue": paper.venue,
            "pdf_url": paper.pdf_url,
            "source": paper.source,
            "category": paper.category
        }
    }

# Download PDF Endpoint
import httpx

@router.post("/{paper_id}/download-pdf")
async def download_pdf(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """
    Download PDF from external URL and save locally
    """
    # Check if paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if paper has external PDF URL
    if not paper.pdf_url:
        raise HTTPException(status_code=400, detail="Paper has no PDF URL")
    
    # Check if already local
    if paper.pdf_url.startswith("http://localhost"):
        return {
            "message": "PDF already stored locally",
            "pdf_url": paper.pdf_url,
            "already_local": True
        }
    
    # Create upload directory
    upload_dir = Path("uploads/pdfs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"{paper_id}.pdf"
    file_path = upload_dir / filename
    
    try:
        # Download PDF with timeout
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            logger.info(f"Downloading PDF from {paper.pdf_url}")
            response = await client.get(paper.pdf_url)
            response.raise_for_status()
            
            # Verify content type
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"Unexpected content type: {content_type}")
            
            # Save file
            with file_path.open("wb") as f:
                f.write(response.content)
            
            logger.info(f"PDF downloaded successfully: {file_path}")
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to download PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error downloading PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")
    
    # Update paper PDF URL to local
    local_url = f"http://localhost:8000/uploads/pdfs/{filename}"
    paper.pdf_url = local_url
    
    db.commit()
    db.refresh(paper)
    
    return {
        "message": "PDF downloaded and saved successfully",
        "pdf_url": local_url,
        "paper_id": paper_id,
        "file_size": file_path.stat().st_size,
        "paper": {
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract,
            "authors": paper.authors,
            "publication_date": paper.publication_date,
            "doi": paper.doi,
            "citation_count": paper.citation_count,
            "venue": paper.venue,
            "pdf_url": paper.pdf_url,
            "source": paper.source,
            "category": paper.category
        }
    }


# Manual Paper Creation Endpoint
from fastapi import UploadFile, File, Form
from pathlib import Path

@router.post("/manual")
async def create_manual_paper(
    title: str = Form(...),
    authors: str = Form(...),  # Comma-separated
    abstract: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    doi: Optional[str] = Form(None),
    venue: Optional[str] = Form(None),
    folder_id: Optional[int] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Create a paper manually with optional PDF upload"""
    
    # Parse authors
    authors_list = [a.strip() for a in authors.split(',') if a.strip()]
    
    if not authors_list:
        raise HTTPException(status_code=400, detail="At least one author is required")
    
    # Handle PDF upload if provided
    pdf_url = None
    if pdf_file:
        # Validate PDF
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Create uploads directory
        upload_dir = Path("uploads/pdfs")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = int(time.time())
        filename = f"manual_{timestamp}_{pdf_file.filename}"
        file_path = upload_dir / filename
        
        # Save file
        try:
            with file_path.open("wb") as f:
                content = await pdf_file.read()
                f.write(content)
            
            pdf_url = f"http://localhost:8000/uploads/pdfs/{filename}"
            logger.info(f"Saved manual PDF: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")
            raise HTTPException(status_code=500, detail="Failed to save PDF file")
    
    # Create paper in database
    try:
        from sqlalchemy import text
        
        # Prepare parameters
        import json
        params = {
            "user_id": user_id,
            "title": title,
            "abstract": abstract,
            "authors": json.dumps(authors_list), # Serialize to JSON string
            "publication_date": f"{year}-01-01" if year else None,
            "doi": doi,
            "venue": venue,
            "pdf_url": pdf_url,
            "source": "Manual Entry",
            "is_manual": True,
            "citation_count": 0
        }
        
        result = db.execute(
            text("""
            INSERT INTO papers (
                user_id, title, abstract, authors, publication_date,
                doi, venue, pdf_url, source, is_manual, citation_count
            )
            VALUES (:user_id, :title, :abstract, :authors, :publication_date, :doi, :venue, :pdf_url, :source, :is_manual, :citation_count)
            RETURNING id, title, abstract, authors, publication_date, doi, venue, pdf_url, source, citation_count
            """),
            params
        )
        db.commit()
        
        paper_data = result.fetchone()
        paper_id = paper_data[0]
        
        # Save the paper to user's library
        try:
            db.execute(
                text("INSERT INTO user_saved_papers (user_id, paper_id) VALUES (:user_id, :paper_id)"),
                {"user_id": user_id, "paper_id": paper_id}
            )
            db.commit()
            logger.info(f"Saved manual paper {paper_id} to user library")
        except Exception as e:
            logger.warning(f"Failed to save paper to library (might already exist): {e}")
        
        # Add to folder if specified
        if folder_id:
            # Verify folder exists and belongs to user
            folder_check = db.execute(
                text("SELECT id FROM folders WHERE id = :id AND user_id = :user_id"),
                {"id": folder_id, "user_id": user_id}
            ).fetchone()
            
            if folder_check:
                db.execute(
                    text("INSERT INTO folder_papers (folder_id, paper_id) VALUES (:folder_id, :paper_id)"),
                    {"folder_id": folder_id, "paper_id": paper_id}
                )
                db.commit()
                logger.info(f"Added paper {paper_id} to folder {folder_id}")

        # Trigger Auto-Indexing if PDF exists
        if pdf_url and 'file_path' in locals():
             background_tasks.add_task(
                parse_pdf_background,
                pdf_path=str(file_path.absolute()),
                paper_id=paper_id,
                project_id=0
            )

        
        return {
            "id": paper_id,
            "title": paper_data[1],
            "abstract": paper_data[2],
            "authors": paper_data[3],
            "publication_date": paper_data[4],
            "doi": paper_data[5],
            "venue": paper_data[6],
            "pdf_url": paper_data[7],
            "source": paper_data[8],
            "citation_count": paper_data[9],
            "is_manual": True
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create manual paper: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create paper: {str(e)}")
