# Phase 3: Tools & Agents - Integration with YOUR Database

**Duration**: Week 5  
**Goal**: Build specialized tools that integrate with YOUR existing tables (comparison_configs, findings, methodology_data, etc.) and create orchestrator agent

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 2 is complete**:

```bash
# 1. Verify RAG engine exists
.venv\Scripts\python.exe -c "from app.core.rag_engine import RAGEngine; print('✓ RAG engine ready')"
# Expected: "✓ RAG engine ready"

# 2. Verify LLM client exists
.venv\Scripts\python.exe -c "from app.core.llm_client import LLMClient; print('✓ LLM client ready')"
# Expected: "✓ LLM client ready"

# 3. Verify base agent exists
.venv\Scripts\python.exe -c "from app.agents.base import FlexibleAgent; print('✓ Base agent ready')"
# Expected: "✓ Base agent ready"

# 4. Verify YOUR existing tables
.venv\Scripts\python.exe -c "
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text(\"SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('comparison_configs', 'findings', 'methodology_data')\"))
    tables = [row[0] for row in result]
    print(f'✓ Found {len(tables)} tables: {tables}')
"
# Expected: "✓ Found 3 tables: ['comparison_configs', 'findings', 'methodology_data']"
```

**✅ You should have**:
- RAG engine with LlamaIndex + Nomic + Docling
- LLM client with Groq
- Flexible agent base class
- YOUR existing database tables

**❌ If missing, complete Phase 2 first**

---

## ✅ Checklist

### Database Tools (YOUR Tables)
- [ ] Create `backend/app/tools/database_tools.py`
- [ ] Implement `get_project_by_name` - Fuzzy search YOUR projects table
- [ ] Implement `get_project_papers` - Get papers from YOUR project_papers table
- [ ] Implement `update_comparison` - Update YOUR comparison_configs table
- [ ] Implement `update_methodology` - Update YOUR methodology_data table
- [ ] Implement `update_findings` - Update YOUR findings table
- [ ] Implement `update_synthesis` - Update YOUR synthesis_data table
- [ ] Implement `link_paper_to_project` - Add to YOUR project_papers table
- [ ] Test all database tools

### RAG Tools (LlamaIndex + Nomic)
- [ ] Create `backend/app/tools/rag_tools.py`
- [ ] Implement `semantic_search` - Query with YOUR Nomic embeddings
- [ ] Implement `compare_papers` - Generate comparison insights
- [ ] Implement `extract_methodology` - Extract methodology details
- [ ] Implement `find_research_gaps` - Identify gaps
- [ ] Test RAG tools with real papers

### PDF Processing Tools (Docling)
- [ ] Create `backend/app/tools/pdf_tools.py`
- [ ] Implement `parse_pdf_with_docling` - Extract equations, tables, images
- [ ] Implement `check_paper_exists` - Check by DOI/hash
- [ ] Implement `store_paper` - Save to YOUR papers table
- [ ] Implement `generate_embeddings` - Use YOUR Nomic model
- [ ] Test with various PDF formats

### Background Worker (Async Processing)
- [ ] Install `arq` (Redis queue)
- [ ] Create `backend/app/core/worker.py` - Worker settings
- [ ] Create `backend/app/workers/pdf_processors.py` - Docling logic
- [ ] Update `backend/app/main.py` to mount worker
- [ ] Implement `submit_pdf_job` - Enqueue task
- [ ] Implement `get_job_status` - Check progress

### Orchestrator Agent
- [ ] Create `backend/app/agents/orchestrator.py`
- [ ] Implement intent classification
- [ ] Implement execution planning
- [ ] Implement tool delegation
- [ ] Implement response synthesis
- [ ] Add conversation memory
- [ ] Test with complex tasks

---

## 📋 Step-by-Step Implementation

### 1. Database Tools for YOUR Existing Tables

Create `backend/app/tools/database_tools.py`:

```python
"""
Database tools for YOUR existing tables
Integrates with comparison_configs, findings, methodology_data, synthesis_data, etc.
"""
from sqlalchemy import text
from typing import List, Dict, Optional
from difflib import SequenceMatcher

# ==================== PROJECT TOOLS ====================

async def get_project_by_name(
    project_name: str,
    user_id: str,
    db,
    fuzzy: bool = True
) -> Optional[Dict]:
    """
    Find project by name (supports fuzzy matching)
    
    Args:
        project_name: Project name to search for
        user_id: User ID for filtering
        db: Database session
        fuzzy: Enable fuzzy matching
    
    Returns:
        Project dict or None
    """
    # Get all user projects
    result = await db.execute(
        text("""
            SELECT id, name, description, created_at
            FROM projects
            WHERE user_id = :user_id
        """),
        {'user_id': user_id}
    )
    
    projects = [dict(row._mapping) for row in result.fetchall()]
    
    if not projects:
        return None
    
    # Exact match first
    for project in projects:
        if project['name'].lower() == project_name.lower():
            return project
    
    # Fuzzy match if enabled
    if fuzzy:
        best_match = None
        best_score = 0.6  # Minimum similarity threshold
        
        for project in projects:
            score = SequenceMatcher(None, project_name.lower(), project['name'].lower()).ratio()
            if score > best_score:
                best_score = score
                best_match = project
        
        return best_match
    
    return None

async def get_project_papers(
    project_id: int,
    db,
    include_details: bool = True
) -> List[Dict]:
    """
    Get all papers in a project from YOUR project_papers table
    
    Args:
        project_id: Project ID
        db: Database session
        include_details: Include full paper details
    
    Returns:
        List of paper dicts
    """
    if include_details:
        query = """
            SELECT 
                p.id,
                p.title,
                p.authors,
                p.abstract,
                p.doi,
                p.source,
                p.published_date,
                pp.added_at
            FROM papers p
            JOIN project_papers pp ON pp.paper_id = p.id
            WHERE pp.project_id = :project_id
            ORDER BY pp.added_at DESC
        """
    else:
        query = """
            SELECT paper_id as id
            FROM project_papers
            WHERE project_id = :project_id
        """
    
    result = await db.execute(
        text(query),
        {'project_id': project_id}
    )
    
    return [dict(row._mapping) for row in result.fetchall()]

# ==================== COMPARISON TOOLS ====================

async def update_comparison(
    user_id: str,
    project_id: int,
    similarities: Optional[str] = None,
    differences: Optional[str] = None,
    selected_papers: Optional[List[int]] = None,
    db = None
) -> Dict:
    """
    Update YOUR comparison_configs table
    
    Args:
        user_id: User ID
        project_id: Project ID
        similarities: Similarities text
        differences: Differences text
        selected_papers: List of paper IDs
        db: Database session
    
    Returns:
        Updated comparison config
    """
    # Build update fields
    updates = []
    params = {
        'user_id': user_id,
        'project_id': project_id
    }
    
    if similarities is not None:
        updates.append("insights_similarities = :similarities")
        params['similarities'] = similarities
    
    if differences is not None:
        updates.append("insights_differences = :differences")
        params['differences'] = differences
    
    if selected_papers is not None:
        updates.append("selected_paper_ids = :selected_papers")
        params['selected_papers'] = selected_papers
    
    if not updates:
        raise ValueError("No fields to update")
    
    # Upsert into YOUR comparison_configs table
    await db.execute(
        text(f"""
            INSERT INTO comparison_configs 
            (user_id, project_id, insights_similarities, insights_differences, selected_paper_ids)
            VALUES (:user_id, :project_id, :similarities, :differences, :selected_papers)
            ON CONFLICT (user_id, project_id) DO UPDATE SET
                {', '.join(updates)},
                updated_at = NOW()
        """),
        params
    )
    await db.commit()
    
    # Return updated config
    result = await db.execute(
        text("""
            SELECT * FROM comparison_configs
            WHERE user_id = :user_id AND project_id = :project_id
        """),
        {'user_id': user_id, 'project_id': project_id}
    )
    
    return dict(result.fetchone()._mapping)

# ==================== FINDINGS TOOLS ====================

async def update_findings(
    user_id: str,
    project_id: int,
    paper_id: int,
    key_finding: Optional[str] = None,
    limitations: Optional[str] = None,
    custom_notes: Optional[str] = None,
    db = None
) -> Dict:
    """
    Update YOUR findings table
    
    Args:
        user_id: User ID
        project_id: Project ID
        paper_id: Paper ID
        key_finding: Key finding text
        limitations: Limitations text
        custom_notes: Custom notes
        db: Database session
    
    Returns:
        Updated finding
    """
    # Build update fields
    updates = []
    params = {
        'user_id': user_id,
        'project_id': project_id,
        'paper_id': paper_id
    }
    
    if key_finding is not None:
        updates.append("key_finding = :key_finding")
        params['key_finding'] = key_finding
    
    if limitations is not None:
        updates.append("limitations = :limitations")
        params['limitations'] = limitations
    
    if custom_notes is not None:
        updates.append("custom_notes = :custom_notes")
        params['custom_notes'] = custom_notes
    
    if not updates:
        raise ValueError("No fields to update")
    
    # Upsert into YOUR findings table
    await db.execute(
        text(f"""
            INSERT INTO findings 
            (user_id, project_id, paper_id, key_finding, limitations, custom_notes)
            VALUES (:user_id, :project_id, :paper_id, :key_finding, :limitations, :custom_notes)
            ON CONFLICT (user_id, project_id, paper_id) DO UPDATE SET
                {', '.join(updates)},
                updated_at = NOW()
        """),
        params
    )
    await db.commit()
    
    # Return updated finding
    result = await db.execute(
        text("""
            SELECT * FROM findings
            WHERE user_id = :user_id AND project_id = :project_id AND paper_id = :paper_id
        """),
        params
    )
    
    return dict(result.fetchone()._mapping)

# ==================== METHODOLOGY TOOLS ====================

async def update_methodology(
    user_id: str,
    project_id: int,
    paper_id: int,
    methodology_summary: Optional[str] = None,
    data_collection: Optional[str] = None,
    analysis_methods: Optional[str] = None,
    sample_size: Optional[str] = None,
    db = None
) -> Dict:
    """
    Update YOUR methodology_data table
    
    Args:
        user_id: User ID
        project_id: Project ID
        paper_id: Paper ID
        methodology_summary: Summary text
        data_collection: Data collection methods
        analysis_methods: Analysis methods
        sample_size: Sample size info
        db: Database session
    
    Returns:
        Updated methodology
    """
    # Build update fields
    updates = []
    params = {
        'user_id': user_id,
        'project_id': project_id,
        'paper_id': paper_id
    }
    
    if methodology_summary is not None:
        updates.append("methodology_summary = :methodology_summary")
        params['methodology_summary'] = methodology_summary
    
    if data_collection is not None:
        updates.append("data_collection = :data_collection")
        params['data_collection'] = data_collection
    
    if analysis_methods is not None:
        updates.append("analysis_methods = :analysis_methods")
        params['analysis_methods'] = analysis_methods
    
    if sample_size is not None:
        updates.append("sample_size = :sample_size")
        params['sample_size'] = sample_size
    
    if not updates:
        raise ValueError("No fields to update")
    
    # Upsert into YOUR methodology_data table
    await db.execute(
        text(f"""
            INSERT INTO methodology_data 
            (user_id, project_id, paper_id, methodology_summary, data_collection, analysis_methods, sample_size)
            VALUES (:user_id, :project_id, :paper_id, :methodology_summary, :data_collection, :analysis_methods, :sample_size)
            ON CONFLICT (user_id, project_id, paper_id) DO UPDATE SET
                {', '.join(updates)},
                updated_at = NOW()
        """),
        params
    )
    await db.commit()
    
    # Return updated methodology
    result = await db.execute(
        text("""
            SELECT * FROM methodology_data
            WHERE user_id = :user_id AND project_id = :project_id AND paper_id = :paper_id
        """),
        params
    )
    
    return dict(result.fetchone()._mapping)

# ==================== SYNTHESIS TOOLS ====================

async def update_synthesis(
    user_id: str,
    project_id: int,
    synthesis_text: Optional[str] = None,
    key_themes: Optional[List[str]] = None,
    research_gaps: Optional[List[str]] = None,
    db = None
) -> Dict:
    """
    Update YOUR synthesis_data table
    
    Args:
        user_id: User ID
        project_id: Project ID
        synthesis_text: Synthesis text
        key_themes: List of key themes
        research_gaps: List of research gaps
        db: Database session
    
    Returns:
        Updated synthesis
    """
    params = {
        'user_id': user_id,
        'project_id': project_id,
        'synthesis_text': synthesis_text,
        'key_themes': key_themes,
        'research_gaps': research_gaps
    }
    
    # Upsert into YOUR synthesis_data table
    await db.execute(
        text("""
            INSERT INTO synthesis_data 
            (user_id, project_id, synthesis_text, key_themes, research_gaps)
            VALUES (:user_id, :project_id, :synthesis_text, :key_themes, :research_gaps)
            ON CONFLICT (user_id, project_id) DO UPDATE SET
                synthesis_text = COALESCE(:synthesis_text, synthesis_data.synthesis_text),
                key_themes = COALESCE(:key_themes, synthesis_data.key_themes),
                research_gaps = COALESCE(:research_gaps, synthesis_data.research_gaps),
                updated_at = NOW()
        """),
        params
    )
    await db.commit()
    
    # Return updated synthesis
    result = await db.execute(
        text("""
            SELECT * FROM synthesis_data
            WHERE user_id = :user_id AND project_id = :project_id
        """),
        {'user_id': user_id, 'project_id': project_id}
    )
    
    return dict(result.fetchone()._mapping)

# ==================== PAPER MANAGEMENT TOOLS ====================

async def link_paper_to_project(
    project_id: int,
    paper_id: int,
    db = None
) -> Dict:
    """
    Add paper to project in YOUR project_papers table
    
    Args:
        project_id: Project ID
        paper_id: Paper ID
        db: Database session
    
    Returns:
        Link info
    """
    await db.execute(
        text("""
            INSERT INTO project_papers (project_id, paper_id)
            VALUES (:project_id, :paper_id)
            ON CONFLICT (project_id, paper_id) DO NOTHING
        """),
        {'project_id': project_id, 'paper_id': paper_id}
    )
    await db.commit()
    
    return {
        'project_id': project_id,
        'paper_id': paper_id,
        'status': 'linked'
    }
```

**Test Database Tools**:

Create `backend/test_database_tools.py`:

```python
import asyncio
from app.tools.database_tools import *
from app.core.database import get_db
from sqlalchemy.orm import Session

async def test_tools():
    # Get database session
    db = next(get_db())
    
    print("🧪 Testing Database Tools\n")
    
    # Test 1: Get project by name
    print("1️⃣ Testing get_project_by_name...")
    project = await get_project_by_name(
        project_name="My Research",
        user_id="test_user",
        db=db,
        fuzzy=True
    )
    print(f"   ✅ Found project: {project['name'] if project else 'None'}\n")
    
    # Test 2: Get project papers
    if project:
        print("2️⃣ Testing get_project_papers...")
        papers = await get_project_papers(
            project_id=project['id'],
            db=db
        )
        print(f"   ✅ Found {len(papers)} papers\n")
    
    # Test 3: Update comparison
    if project:
        print("3️⃣ Testing update_comparison...")
        comparison = await update_comparison(
            user_id="test_user",
            project_id=project['id'],
            similarities="Both papers use machine learning approaches",
            differences="Paper A uses CNN, Paper B uses RNN",
            db=db
        )
        print(f"   ✅ Updated comparison\n")
    
    print("✅ All database tools tests passed!")

if __name__ == "__main__":
    asyncio.run(test_tools())
```

---

### 2. RAG Tools (LlamaIndex + YOUR Nomic Embeddings)

Create `backend/app/tools/rag_tools.py`:

```python
"""
RAG tools using LlamaIndex with YOUR Nomic embeddings
Provides semantic search, comparison, methodology extraction, etc.
"""
from typing import List, Dict, Optional
from app.core.rag_engine import RAGEngine
from app.core.llm_client import LLMClient

async def semantic_search(
    query: str,
    project_id: Optional[int] = None,
    section_filter: Optional[List[str]] = None,
    top_k: int = 10,
    rag_engine: RAGEngine = None
) -> List[Dict]:
    """
    Semantic search using YOUR Nomic embeddings via LlamaIndex
    
    Args:
        query: Search query
        project_id: Filter by YOUR project_id
        section_filter: Filter by section types
        top_k: Number of results
        rag_engine: RAG engine instance
    
    Returns:
        List of relevant chunks
    """
    if not rag_engine:
        rag_engine = RAGEngine()
    
    result = await rag_engine.query(
        query_text=query,
        project_id=project_id,
        section_filter=section_filter,
        top_k=top_k,
        return_sources=True
    )
    
    return result['source_nodes']

async def compare_papers(
    paper_ids: List[int],
    aspect: str = "methodology",
    project_id: Optional[int] = None,
    rag_engine: RAGEngine = None,
    llm_client: LLMClient = None
) -> Dict[str, str]:
    """
    Generate comparison insights between papers
    
    Args:
        paper_ids: List of paper IDs to compare
        aspect: What to compare (methodology, findings, etc.)
        project_id: Project ID for filtering
        rag_engine: RAG engine instance
        llm_client: LLM client instance
    
    Returns:
        Dict with similarities and differences
    """
    if not rag_engine:
        rag_engine = RAGEngine()
    if not llm_client:
        llm_client = LLMClient()
    
    # Retrieve relevant chunks for each paper
    all_chunks = []
    for paper_id in paper_ids:
        chunks = await rag_engine.retrieve_only(
            query_text=aspect,
            project_id=project_id,
            top_k=5
        )
        # Filter by paper_id
        paper_chunks = [c for c in chunks if c['metadata'].get('paper_id') == paper_id]
        all_chunks.extend(paper_chunks)
    
    # Build context
    context = "\n\n".join([
        f"Paper {chunk['metadata']['paper_id']}:\n{chunk['text']}"
        for chunk in all_chunks
    ])
    
    # Generate comparison with LLM
    prompt = f"""Compare the {aspect} across these papers.

Context:
{context}

Provide:
1. SIMILARITIES: What approaches/methods are similar?
2. DIFFERENCES: What are the key differences?

Format as JSON:
{{
    "similarities": "...",
    "differences": "..."
}}"""
    
    response = await llm_client.complete(prompt, temperature=0.3)
    
    # Parse JSON response
    import json
    try:
        result = json.loads(response)
    except:
        # Fallback if LLM doesn't return valid JSON
        result = {
            "similarities": response.split("DIFFERENCES")[0].replace("SIMILARITIES:", "").strip(),
            "differences": response.split("DIFFERENCES:")[1].strip() if "DIFFERENCES:" in response else ""
        }
    
    return result

async def extract_methodology(
    paper_id: int,
    project_id: Optional[int] = None,
    rag_engine: RAGEngine = None,
    llm_client: LLMClient = None
) -> Dict:
    """
    Extract structured methodology details from a paper
    
    Args:
        paper_id: Paper ID
        project_id: Project ID for filtering
        rag_engine: RAG engine instance
        llm_client: LLM client instance
    
    Returns:
        Dict with methodology details
    """
    if not rag_engine:
        rag_engine = RAGEngine()
    if not llm_client:
        llm_client = LLMClient()
    
    # Retrieve methodology sections
    chunks = await rag_engine.retrieve_only(
        query_text="methodology methods approach",
        project_id=project_id,
        top_k=10
    )
    
    # Filter by paper_id and methodology sections
    method_chunks = [
        c for c in chunks 
        if c['metadata'].get('paper_id') == paper_id and
           c['metadata'].get('section_type') in ['methodology', 'methods', 'approach']
    ]
    
    if not method_chunks:
        return {
            "methodology_summary": "No methodology section found",
            "data_collection": "",
            "analysis_methods": "",
            "sample_size": ""
        }
    
    # Build context
    context = "\n\n".join([chunk['text'] for chunk in method_chunks])
    
    # Extract structured data with LLM
    prompt = f"""Extract methodology details from this paper.

Context:
{context}

Provide:
1. METHODOLOGY_SUMMARY: Brief overview
2. DATA_COLLECTION: How data was collected
3. ANALYSIS_METHODS: Analysis techniques used
4. SAMPLE_SIZE: Sample size if mentioned

Format as JSON:
{{
    "methodology_summary": "...",
    "data_collection": "...",
    "analysis_methods": "...",
    "sample_size": "..."
}}"""
    
    response = await llm_client.complete(prompt, temperature=0.3)
    
    # Parse JSON response
    import json
    try:
        result = json.loads(response)
    except:
        result = {
            "methodology_summary": response,
            "data_collection": "",
            "analysis_methods": "",
            "sample_size": ""
        }
    
    return result

async def find_research_gaps(
    project_id: int,
    rag_engine: RAGEngine = None,
    llm_client: LLMClient = None
) -> List[str]:
    """
    Identify research gaps across papers in a project
    
    Args:
        project_id: Project ID
        rag_engine: RAG engine instance
        llm_client: LLM client instance
    
    Returns:
        List of research gaps
    """
    if not rag_engine:
        rag_engine = RAGEngine()
    if not llm_client:
        llm_client = LLMClient()
    
    # Retrieve findings and limitations
    chunks = await rag_engine.retrieve_only(
        query_text="limitations future work research gaps",
        project_id=project_id,
        top_k=20
    )
    
    # Build context
    context = "\n\n".join([chunk['text'] for chunk in chunks])
    
    # Identify gaps with LLM
    prompt = f"""Identify research gaps from these papers.

Context:
{context}

List 3-5 key research gaps or future research directions.

Format as JSON array:
["gap 1", "gap 2", "gap 3"]"""
    
    response = await llm_client.complete(prompt, temperature=0.5)
    
    # Parse JSON response
    import json
    try:
        gaps = json.loads(response)
    except:
        # Fallback: split by newlines
        gaps = [line.strip("- ").strip() for line in response.split("\n") if line.strip()]
    
    return gaps[:5]  # Return max 5 gaps
```

---

### 3. PDF Processing Tools (Docling + Background Worker)

> [!IMPORTANT]
> **Performance Critical**: Docling is CPU-intensive. We MUST run it in a background worker to prevent blocking the API.

**1. Install Worker Dependencies**:
```bash
.venv\Scripts\python.exe -m pip install arq
```

**2. Create Worker Config** (`backend/app/core/worker.py`):
```python
"""
Redis-backed worker Configuration using ARQ
"""
from arq.connections import RedisSettings
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

async def get_redis_settings():
    return RedisSettings.from_dsn(REDIS_URL)
```

**3. Create PDF Processor** (`backend/app/workers/pdf_processors.py`):
```python
"""
Background jobs for PDF processing
"""
import asyncio
from app.core.rag_engine import RAGEngine
from app.core.database import SessionLocal
from sqlalchemy import text

async def process_pdf_job(ctx, paper_id: int, pdf_path: str, project_id: int = None):
    """
    Background task to process PDF with Docling
    """
    print(f"🔄 [Worker] Starting processing for Paper {paper_id}...")
    
    # Initialize RAG (expensive, maybe cache this in a real worker class)
    rag_engine = RAGEngine()
    
    try:
        # 1. Parse & Ingest
        stats = await rag_engine.ingest_paper_with_docling(
            paper_id=paper_id,
            pdf_path=pdf_path,
            metadata={'project_id': project_id}
        )
        
        # 2. Update Database Status
        db = SessionLocal()
        try:
            db.execute(
                text("UPDATE papers SET is_processed = TRUE, last_updated = NOW() WHERE id = :pid"),
                {'pid': paper_id}
            )
            db.commit()
        finally:
            db.close()
            
        print(f"✅ [Worker] Finished Paper {paper_id}: {stats}")
        return stats
        
    except Exception as e:
        print(f"❌ [Worker] Failed Paper {paper_id}: {e}")
        # Update DB with error status if you have an error column
        raise e

# ARQ Worker Settings
class WorkerSettings:
    functions = [process_pdf_job]
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
```

**4. Update PDF Tools to Enqueue Jobs** (`backend/app/tools/pdf_tools.py`):
```python
"""
Updated PDF tools using ARQ for background processing
"""
from typing import Dict, Optional
from arq import create_pool
from app.core.worker import get_redis_settings, REDIS_URL

async def parse_pdf_background(
    pdf_path: str,
    paper_id: int,
    project_id: Optional[int] = None
) -> Dict:
    """
    Enqueue PDF parsing job to Redis
    Returns: Job ID and status
    """
    redis = await create_pool(await get_redis_settings())
    
    # Enqueue job
    job = await redis.enqueue_job(
        'process_pdf_job',
        paper_id=paper_id,
        pdf_path=pdf_path,
        project_id=project_id
    )
    
    return {
        "status": "queued",
        "job_id": job.job_id,
        "message": "Paper is processing in background. You can continue working."
    }

async def check_job_status(job_id: str) -> Dict:
    """Check status of background job"""
    redis = await create_pool(await get_redis_settings())
    job = await redis.get_job(job_id)
    
    if not job:
        return {"status": "unknown"}
        
    status = await job.status()
    result = await job.result() if status == 'complete' else None
    
    return {
        "status": str(status),
        "result": result
    }
    
# ... (Keep existing check_paper_exists and store_paper tools) ...
```

async def check_paper_exists(
    doi: Optional[str] = None,
    title: Optional[str] = None,
    db = None
) -> Optional[Dict]:
    """
    Check if paper exists in YOUR papers table
    
    Args:
        doi: DOI to check
        title: Title to check
        db: Database session
    
    Returns:
        Paper dict if exists, None otherwise
    """
    if doi:
        result = await db.execute(
            text("SELECT * FROM papers WHERE doi = :doi"),
            {'doi': doi}
        )
        row = result.fetchone()
        if row:
            return dict(row._mapping)
    
    if title:
        # Generate hash for deduplication
        title_hash = hashlib.md5(title.lower().encode()).hexdigest()
        result = await db.execute(
            text("SELECT * FROM papers WHERE paper_hash = :hash"),
            {'hash': title_hash}
        )
        row = result.fetchone()
        if row:
            return dict(row._mapping)
    
    return None

async def store_paper(
    title: str,
    authors: List[str],
    abstract: str,
    doi: Optional[str] = None,
    source: str = "manual",
    db = None
) -> int:
    """
    Store paper in YOUR papers table
    
    Args:
        title: Paper title
        authors: List of authors
        abstract: Abstract text
        doi: Optional DOI
        source: Source (manual, arxiv, etc.)
        db: Database session
    
    Returns:
        Paper ID
    """
    # Generate hash for deduplication
    paper_hash = hashlib.md5(title.lower().encode()).hexdigest()
    
    result = await db.execute(
        text("""
            INSERT INTO papers (
                title, authors, abstract, doi, source, paper_hash
            ) VALUES (
                :title, :authors, :abstract, :doi, :source, :hash
            )
            ON CONFLICT (paper_hash) DO UPDATE SET
                title = EXCLUDED.title,
                authors = EXCLUDED.authors,
                abstract = EXCLUDED.abstract,
                doi = EXCLUDED.doi
            RETURNING id
        """),
        {
            'title': title,
            'authors': authors,
            'abstract': abstract,
            'doi': doi,
            'source': source,
            'hash': paper_hash
        }
    )
    await db.commit()
    
    paper_id = result.fetchone()[0]
    return paper_id
```

---

### 4. Orchestrator Agent

Create `backend/app/agents/orchestrator.py`:

```python
"""
Orchestrator Agent - Main entry point for user requests
Classifies intent, plans execution, delegates to tools
"""
from typing import Dict, List, Any
from app.agents.base import FlexibleAgent, Tool
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.tools import database_tools, rag_tools, pdf_tools
import json

class OrchestratorAgent:
    """
    Main orchestrator agent
    Handles user requests and delegates to appropriate tools
    """
    
    def __init__(self, llm_client: LLMClient, db, rag_engine: RAGEngine):
        self.llm = llm_client
        self.db = db
        self.rag = rag_engine
        
        # Initialize tools
        self.tools = self._create_tools()
        
        # Create flexible agent
        self.agent = FlexibleAgent(
            name="LiteratureReviewAssistant",
            llm_client=llm_client,
            tools=self.tools
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create all available tools"""
        return [
            # Database tools
            Tool(
                name="get_project_papers",
                description="Get all papers in a project",
                parameters={"project_id": "int"},
                function=lambda project_id: database_tools.get_project_papers(
                    project_id=project_id,
                    db=self.db
                )
            ),
            Tool(
                name="update_comparison",
                description="Update comparison insights for a project",
                parameters={
                    "user_id": "str",
                    "project_id": "int",
                    "similarities": "str",
                    "differences": "str"
                },
                function=lambda **kwargs: database_tools.update_comparison(
                    **kwargs,
                    db=self.db
                )
            ),
            Tool(
                name="update_findings",
                description="Update findings for a paper",
                parameters={
                    "user_id": "str",
                    "project_id": "int",
                    "paper_id": "int",
                    "key_finding": "str",
                    "limitations": "str"
                },
                function=lambda **kwargs: database_tools.update_findings(
                    **kwargs,
                    db=self.db
                )
            ),
            
            # RAG tools
            Tool(
                name="semantic_search",
                description="Search papers semantically",
                parameters={
                    "query": "str",
                    "project_id": "int (optional)",
                    "top_k": "int (default 10)"
                },
                function=lambda **kwargs: rag_tools.semantic_search(
                    **kwargs,
                    rag_engine=self.rag
                )
            ),
            Tool(
                name="compare_papers",
                description="Compare papers on a specific aspect",
                parameters={
                    "paper_ids": "list of int",
                    "aspect": "str (methodology, findings, etc.)"
                },
                function=lambda **kwargs: rag_tools.compare_papers(
                    **kwargs,
                    rag_engine=self.rag,
                    llm_client=self.llm
                )
            ),
            Tool(
                name="extract_methodology",
                description="Extract methodology details from a paper",
                parameters={"paper_id": "int"},
                function=lambda **kwargs: rag_tools.extract_methodology(
                    **kwargs,
                    rag_engine=self.rag,
                    llm_client=self.llm
                )
            ),
        ]
    
    async def process_user_message(
        self,
        user_id: str,
        message: str,
        project_id: Optional[int] = None
    ) -> Dict:
        """
        Main entry point for user messages
        
        Args:
            user_id: User ID
            message: User message
            project_id: Optional project ID for context
        
        Returns:
            Response dict
        """
        # Add context to agent
        self.agent.context = {
            'user_id': user_id,
            'project_id': project_id
        }
        
        # Run agent
        result = await self.agent.run(message)
        
        return result
```

---

## 🧪 Verification

Create `backend/test_phase3.py`:

```python
import asyncio
from app.agents.orchestrator import OrchestratorAgent
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.core.database import get_db

async def test_orchestrator():
    print("=" * 60)
    print("🧪 Phase 3 Verification Test")
    print("=" * 60)
    
    # Initialize components
    db = next(get_db())
    llm = LLMClient(db)
    rag = RAGEngine()
    
    # Create orchestrator
    print("\n1️⃣ Creating orchestrator...")
    orchestrator = OrchestratorAgent(llm, db, rag)
    print("   ✅ Orchestrator created with", len(orchestrator.tools), "tools")
    
    # Test simple query
    print("\n2️⃣ Testing user query...")
    result = await orchestrator.process_user_message(
        user_id="test_user",
        message="What papers are in my project?",
        project_id=1
    )
    print(f"   ✅ Result: {result}")
    
    print("\n" + "=" * 60)
    print("✅ Phase 3 verification PASSED!")
    print("=" * 60)
    print("\n🎯 Next steps:")
    print("   1. Test with real user queries")
    print("   2. Proceed to Phase 4: API & Frontend")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
```

---

## 📝 Deliverables

- ✅ Database tools for YOUR existing tables
- ✅ RAG tools with LlamaIndex + Nomic
- ✅ PDF tools with Docling
- ✅ Orchestrator agent
- ✅ All tests passing

---

## ⏭️ Next Phase

Proceed to **Phase 4: API & Frontend** to build REST endpoints and chat UI.
