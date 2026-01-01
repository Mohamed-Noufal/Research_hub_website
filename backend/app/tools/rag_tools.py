"""
RAG tools using LlamaIndex with Nomic embeddings
Provides semantic search, comparison, methodology extraction, etc.
"""
from typing import List, Dict, Optional, Any
from app.core.rag_engine import RAGEngine
from app.core.llm_client import LLMClient
from app.core.cache import cached_tool
import json

@cached_tool(ttl=3600)
async def semantic_search(
    query: str,
    project_id: Optional[int] = None,
    section_filter: Optional[List[str]] = None,
    top_k: int = 10,
    scope: str = 'project',
    selected_paper_ids: Optional[List[int]] = None,
    rag_engine: RAGEngine = None
) -> List[Dict]:
    """
    Semantic search using Nomic embeddings via LlamaIndex
    
    Args:
        query: Search query
        project_id: Filter by project_id
        section_filter: Filter by section types
        top_k: Number of results
        scope: Search scope ('project', 'library', 'selection')
        selected_paper_ids: List of paper IDs if scope is 'selection'
        rag_engine: RAG engine instance
    
    Returns:
        List of relevant chunks
    """
    if not rag_engine:
        rag_engine = RAGEngine()
    
    # Determine filters based on scope
    final_project_id = project_id
    final_paper_ids = None
    
    if scope == 'library':
        final_project_id = None # Search everything
    elif scope == 'selection':
        final_paper_ids = selected_paper_ids
        final_project_id = None # Search specifically these papers, ignore project boundary
    
    result = await rag_engine.query(
        query_text=query,
        project_id=final_project_id,
        paper_ids=final_paper_ids,
        section_filter=section_filter,
        top_k=top_k,
        return_sources=True
    )
    
    
    return result.get('source_nodes', [])

@cached_tool(ttl=3600)
async def get_paper_sections(
    section_types: List[str],
    paper_ids: Optional[List[int]] = None,
    project_id: Optional[int] = None,
    scope: str = 'project',
    selected_paper_ids: Optional[List[int]] = None,
    rag_engine: RAGEngine = None
) -> List[Dict]:
    """
    Retrieves full text of specific sections (Methodology, Results, etc.) 
    from a list of papers. Use this for structured summaries and comparisons.
    """
    if not rag_engine:
        rag_engine = RAGEngine()
        
    # Determine filters based on scope
    final_project_id = project_id
    final_paper_ids = paper_ids
    
    # Priority: arguments > scope context
    if not final_paper_ids and scope == 'selection':
        final_paper_ids = selected_paper_ids
    
    if scope == 'library':
        final_project_id = None
    elif scope == 'selection':
        final_project_id = None
        
    # Use retrieve_only with section filter but higher top_k to get comprehensive content
    # Note: Ideally this would be a SQL query, but we use retrieve_only with filters for now
    # to leverage the existing engine logic. 
    # To strictly follow plan "SELECT text FROM... WHERE section_type=...", 
    # we can use the engine's query with a 'match all' query text or specialized method.
    
    # Combine section types for query text to help vector search focus
    query_text = " ".join(section_types)
    
    # Using a specialized query or high-k retrieval
    result = await rag_engine.retrieve_only(
        query_text=query_text, 
        project_id=final_project_id,
        paper_ids=final_paper_ids,
        section_filter=section_types, # Explicit filter logic handles lists with IN operator
        top_k=50 # Retrieve enough chunks
    )
    
    # Post-filter strictly by section_type metadata to ensure purity
    # (The vector search might return 'related' sections, we want exact checks if possible,
    # but the engine filter uses 'ExactMatchFilter' so it should be strict already if we pass it)
    
    return result

@cached_tool(ttl=3600)
async def compare_papers(
    paper_ids: List[int],
    aspect: str = "methodology",
    project_id: Optional[int] = None,
    rag_engine: RAGEngine = None,
    llm_client: LLMClient = None
) -> Dict[str, str]:
    """
    Generate comparison insights between papers
    """
    if not rag_engine:
        rag_engine = RAGEngine()
    if not llm_client:
        llm_client = LLMClient()
    
    # Retrieve relevant chunks for each paper
    # We search the 'aspect' for each paper or global search filtered by papers?
    # Iterating per paper might be cleaner to ensure coverage
    
    all_chunks = []
    
    # Optimization: One search filtering by project and papers?
    # LlamaIndex query with metadata filters on paper_id IN [list] might be key
    # For now, let's just do a broad search on the aspect within the project
    # and then filter in memory if the retrieve doesn't support complex 'IN' list easily
    # Or strict loop:
    
    # Let's try broad retrieval first to fill context
    chunks = await rag_engine.retrieve_only(
        query_text=aspect,
        project_id=project_id,
        top_k=15 # enough for a few papers
    )
    
    # Filter for the requested papers
    relevant_chunks = [c for c in chunks if c['metadata'].get('paper_id') in paper_ids]
    
    # If we missed some papers, we might want to query specific to that paper
    # But for now, using what we found
    
    if not relevant_chunks:
        return {"similarities": "Insufficient data found.", "differences": "Insufficient data found."}

    # Build context
    context = "\n\n".join([
        f"Paper {chunk['metadata'].get('paper_id')}:\n{chunk['text']}"
        for chunk in relevant_chunks
    ])
    
    # Generate comparison with LLM
    prompt = f"""Compare the {aspect} across these papers based on the text below.

Context:
{context}

Provide:
1. SIMILARITIES: What approaches/methods are similar?
2. DIFFERENCES: What are the key differences?

Format as JSON:
{{
    "similarities": "...",
    "differences": "..."
}}
"""
    
    response = await llm_client.complete(prompt, temperature=0.3)
    
    # Parse JSON response
    try:
        # LLM might return Markdown JSON code block
        cleaned_response = response.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned_response)
    except:
        # Fallback parsing
        sim_part = response
        diff_part = ""
        if "DIFFERENCES" in response:
            parts = response.split("DIFFERENCES")
            sim_part = parts[0].replace("SIMILARITIES", "").replace(":", "").strip()
            diff_part = parts[1].replace(":", "").strip()
            
        result = {
            "similarities": sim_part,
            "differences": diff_part
        }
    
    return result

@cached_tool(ttl=86400) # Cache strict extraction longer
async def extract_methodology(
    paper_id: int,
    project_id: Optional[int] = None,
    rag_engine: RAGEngine = None,
    llm_client: LLMClient = None
) -> Dict:
    """
    Extract structured methodology details from a paper
    """
    if not rag_engine:
        rag_engine = RAGEngine()
    if not llm_client:
        llm_client = LLMClient()
    
    # Retrieve methodology sections
    # Searching specifically for "methodology" keywords
    chunks = await rag_engine.retrieve_only(
        query_text="methodology methods approach study design",
        project_id=project_id, # Optimize: filter by paper_id if possible in engine, else filter below
        top_k=10
    )
    
    # Filter by paper_id
    method_chunks = [
        c for c in chunks 
        if c['metadata'].get('paper_id') == paper_id
    ]
    
    if not method_chunks:
        return {
            "methodology_summary": "No specific methodology section found.",
            "data_collection": "",
            "analysis_methods": "",
            "sample_size": ""
        }
    
    # Build context
    context = "\n\n".join([chunk['text'] for chunk in method_chunks])
    
    # Extract structured data with LLM
    prompt = f"""Extract methodology details from this paper context.

Context:
{context}

Provide:
1. METHODOLOGY_SUMMARY: Brief overview (1-2 sentences)
2. DATA_COLLECTION: How was data collected?
3. ANALYSIS_METHODS: What analysis techniques were used?
4. SAMPLE_SIZE: Sample size if mentioned (N=?)

Format as JSON:
{{
    "methodology_summary": "...",
    "data_collection": "...",
    "analysis_methods": "...",
    "sample_size": "..."
}}
"""
    
    response = await llm_client.complete(prompt, temperature=0.2)
    
    try:
        cleaned_response = response.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned_response)
    except:
        result = {
            "methodology_summary": response,
            "data_collection": "",
            "analysis_methods": "",
            "sample_size": ""
        }
    
    return result

@cached_tool(ttl=3600)
async def find_research_gaps(
    project_id: int,
    rag_engine: RAGEngine = None,
    llm_client: LLMClient = None
) -> List[str]:
    """
    Identify research gaps across papers in a project
    """
    if not rag_engine:
        rag_engine = RAGEngine()
    if not llm_client:
        llm_client = LLMClient()
    
    # Retrieve findings and limitations
    chunks = await rag_engine.retrieve_only(
        query_text="limitations future work research gaps conclusion",
        project_id=project_id,
        top_k=15
    )
    
    # Build context
    context = "\n\n".join([chunk['text'] for chunk in chunks])
    
    if not context:
        return ["Insufficient data to identify gaps."]

    # Identify gaps with LLM
    prompt = f"""Identify research gaps from these papers contexts.

Context:
{context}

List 3-5 key research gaps or future research directions suitable for a literature review.

Format as JSON array of strings:
["gap 1", "gap 2", "gap 3"]
"""
    
    response = await llm_client.complete(prompt, temperature=0.5)
    
    try:
        cleaned_response = response.replace("```json", "").replace("```", "").strip()
        gaps = json.loads(cleaned_response)
        if isinstance(gaps, list):
            return gaps[:5]
        return [str(gaps)]
    except:
        # Fallback: split by newlines
        gaps = [line.strip("- *").strip() for line in response.split("\n") if line.strip()]
        return gaps[:5]
