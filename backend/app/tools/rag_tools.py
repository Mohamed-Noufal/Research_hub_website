"""
RAG tools using LlamaIndex with Nomic embeddings
Provides semantic search, comparison, methodology extraction, etc.
"""
from typing import List, Dict, Optional, Any
from app.core.rag_engine import RAGEngine
from app.core.llm_client import LLMClient
from app.core.cache import cached_tool
import json
import re

def strip_think_tags(text: str) -> str:
    """
    Strip <think>...</think> tags from Qwen3 model outputs.
    These are chain-of-thought reasoning tags that shouldn't appear in final output.
    """
    if not text:
        return text
    # Remove <think>...</think> blocks (including newlines inside)
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

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
async def search_paper_sections(
    section_types: List[str],
    paper_ids: Optional[List[int]] = None,
    project_id: Optional[int] = None,
    scope: str = 'project',
    selected_paper_ids: Optional[List[int]] = None,
    rag_engine: RAGEngine = None
) -> List[Dict]:
    """
    Semantic search within specific sections (Methodology, Results, etc.) 
    across papers. Use this for finding relevant content by meaning.
    
    NOTE: For exact section retrieval (no search), use literature_tools.get_paper_sections instead.
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
        # Strip Qwen3 <think> tags and Markdown JSON code block
        cleaned_response = strip_think_tags(response)
        cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned_response)
    except:
        # Fallback parsing - also strip think tags
        clean_resp = strip_think_tags(response)
        sim_part = clean_resp
        diff_part = ""
        if "DIFFERENCES" in clean_resp:
            parts = clean_resp.split("DIFFERENCES")
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
    llm_client: LLMClient = None,
    max_retries: int = 2,
    db = None
) -> Dict:
    """
    Extract structured methodology details from a paper.
    Uses paper_sections table directly (no RAG chunks needed).
    """
    from app.schemas.agent_outputs import MethodologyOutput, get_schema_prompt
    from sqlalchemy import text
    
    if not llm_client:
        llm_client = LLMClient()
    
    # Query paper_sections table directly (works without Celery/RAG)
    context = ""
    if db:
        try:
            result = db.execute(text("""
                SELECT section_type, section_title, content 
                FROM paper_sections 
                WHERE paper_id = :paper_id 
                AND section_type IN ('methodology', 'methods', 'abstract', 'introduction', 'other')
                ORDER BY order_index
                LIMIT 5
            """), {'paper_id': paper_id})
            
            sections = result.fetchall()
            if sections:
                context = "\n\n".join([
                    f"[{row[0].upper()}] {row[1]}\n{row[2]}" 
                    for row in sections
                ])
        except Exception as e:
            print(f"Warning: Could not query paper_sections: {e}")
    
    # Fallback to RAG if no sections found
    if not context and rag_engine:
        chunks = await rag_engine.retrieve_only(
            query_text="methodology methods approach study design data collection analysis",
            project_id=project_id,
            top_k=10
        )
        method_chunks = [c for c in chunks if c['metadata'].get('paper_id') == paper_id]
        context = "\n\n".join([chunk['text'] for chunk in method_chunks])
    
    if not context:
        return {
            "methodology_summary": "No methodology content found for this paper.",
            "data_collection": "",
            "analysis_methods": "",
            "sample_size": "",
            "methodology_context": "",
            "approach_novelty": ""
        }
    
    # Schema-aware prompt - explicitly ask for the 3 main UI fields
    prompt = f"""Extract methodology details from this paper context.

Context:
{context}

You MUST extract the following information:
1. **methodology_summary** (REQUIRED): Describe "The Approach" - what methodology/methods does this paper use?
2. **methodology_context** (REQUIRED): Describe "Previous Context" - what prior work or approaches does this build upon?
3. **approach_novelty** (REQUIRED): Explain "Why It's Different" - what makes this approach novel or unique?
4. **data_collection** (optional): How was data collected?
5. **analysis_methods** (optional): What analysis techniques were used?
6. **sample_size** (optional): What was the sample size?

{get_schema_prompt(MethodologyOutput)}

IMPORTANT: Return ONLY valid JSON, no markdown formatting.
"""
    
    # Retry loop with validation
    last_error = None
    for attempt in range(max_retries + 1):
        response = await llm_client.complete(prompt, temperature=0.2)
        
        try:
            # Clean and parse (strip <think> tags from Qwen3 models)
            cleaned = strip_think_tags(response).strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('```')[1]
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            
            # Validate with Pydantic
            result = MethodologyOutput.model_validate_json(cleaned)
            return result.model_dump()
            
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                # Add error feedback to prompt for retry
                prompt = f"""The previous response was invalid: {last_error}

Please try again. Extract methodology details from this paper context.

Context:
{context}

{get_schema_prompt(MethodologyOutput)}

IMPORTANT: Return ONLY valid JSON, no markdown formatting.
"""
    
    # Fallback if all retries fail
    fallback_summary = strip_think_tags(response)[:500] if response else "Extraction failed"
    return {
        "methodology_summary": fallback_summary,
        "data_collection": "",
        "analysis_methods": "",
        "sample_size": "",
        "_validation_error": last_error
    }


@cached_tool(ttl=86400)
async def extract_findings(
    paper_id: int,
    project_id: Optional[int] = None,
    rag_engine: RAGEngine = None,
    llm_client: LLMClient = None,
    max_retries: int = 2,
    db = None
) -> Dict:
    """
    Extract structured findings from a paper.
    Uses paper_sections table directly (no RAG chunks needed).
    """
    from app.schemas.agent_outputs import FindingsOutput, get_schema_prompt
    from sqlalchemy import text
    
    if not llm_client:
        llm_client = LLMClient()
    
    # Query paper_sections table directly
    context = ""
    if db:
        try:
            result = db.execute(text("""
                SELECT section_type, section_title, content 
                FROM paper_sections 
                WHERE paper_id = :paper_id 
                AND section_type IN ('results', 'discussion', 'conclusion', 'abstract', 'other')
                ORDER BY order_index
                LIMIT 5
            """), {'paper_id': paper_id})
            
            sections = result.fetchall()
            if sections:
                context = "\n\n".join([
                    f"[{row[0].upper()}] {row[1]}\n{row[2]}" 
                    for row in sections
                ])
        except Exception as e:
            print(f"Warning: Could not query paper_sections: {e}")
    
    # Fallback to RAG if no sections found
    if not context and rag_engine:
        chunks = await rag_engine.retrieve_only(
            query_text="results findings conclusions key contributions outcomes",
            project_id=project_id,
            top_k=10
        )
        findings_chunks = [c for c in chunks if c['metadata'].get('paper_id') == paper_id]
        context = "\n\n".join([chunk['text'] for chunk in findings_chunks])
    
    if not context:
        return {
            "key_finding": "No findings content found for this paper.",
            "limitations": "",
            "custom_notes": "",
            "evidence_level": None
        }
    
    # Schema-aware prompt
    prompt = f"""Extract the key findings from this paper context.

Context:
{context}

{get_schema_prompt(FindingsOutput)}

IMPORTANT: Return ONLY valid JSON, no markdown formatting.
"""
    
    # Retry loop with validation
    last_error = None
    for attempt in range(max_retries + 1):
        response = await llm_client.complete(prompt, temperature=0.2)
        
        try:
            # Clean and parse (strip <think> tags from Qwen3 models)
            cleaned = strip_think_tags(response).strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('```')[1]
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            
            # Validate with Pydantic
            result = FindingsOutput.model_validate_json(cleaned)
            return result.model_dump()
            
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                prompt = f"""The previous response was invalid: {last_error}

Please try again. Extract the key findings from this paper context.

Context:
{context}

{get_schema_prompt(FindingsOutput)}

IMPORTANT: Return ONLY valid JSON, no markdown formatting.
"""
    
    # Fallback if all retries fail
    fallback_finding = strip_think_tags(response)[:500] if response else "Extraction failed"
    return {
        "key_finding": fallback_finding,
        "limitations": "",
        "custom_notes": "",
        "evidence_level": None,
        "_validation_error": last_error
    }


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
