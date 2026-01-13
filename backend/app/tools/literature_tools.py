"""
Database tools for reading/writing literature review data
Includes tools for all tabs: Methodology, Findings, Comparison, Synthesis, Summary
"""
from sqlalchemy import text
from typing import List, Dict, Optional


# ==================== READ TOOLS ====================

def get_paper_sections(
    paper_id: int,
    section_types: Optional[List[str]] = None,
    user_id: str = None,
    db = None
) -> List[Dict]:
    """
    Get parsed sections/chunks from a paper.
    
    Args:
        paper_id: Paper ID
        section_types: Optional filter, e.g. ['methodology', 'results']
        user_id: User ID for scoping
        db: Database session
    
    Returns:
        List of section dicts with {text, section_type, metadata}
    """
    import json
    
    # Query from LlamaIndex vector store table (data_paper_chunks)
    # Use CAST for proper integer comparison (metadata stores paper_id as int)
    query = """
        SELECT text, metadata_
        FROM data_paper_chunks
        WHERE (metadata_->>'paper_id')::int = :paper_id
           OR metadata_->>'paper_id' = :paper_id_str
    """
    params = {'paper_id': paper_id, 'paper_id_str': str(paper_id)}
    
    result = db.execute(text(query), params)
    
    sections = []
    for row in result.fetchall():
        text_content = row[0]
        metadata_raw = row[1]
        
        # Parse metadata (might be dict or string)
        if isinstance(metadata_raw, str):
            metadata = json.loads(metadata_raw)
        else:
            metadata = metadata_raw or {}
        
        section_type = metadata.get('section_type', 'unknown')
        
        # Filter by section types if specified
        if section_types and section_type not in section_types:
            continue
        
        sections.append({
            'content': text_content,
            'section_type': section_type,
            'section_title': metadata.get('title', ''),
            'paper_id': metadata.get('paper_id'),
            'word_count': len(text_content.split())
        })
    
    return sections


def get_paper_tables(paper_id: int, db = None) -> List[Dict]:
    """Get all tables from a paper"""
    result = db.execute(text("""
        SELECT table_number, caption, content_markdown
        FROM paper_tables
        WHERE paper_id = :paper_id
        ORDER BY order_index
    """), {'paper_id': paper_id})
    return [dict(row._mapping) for row in result.fetchall()]


def get_paper_equations(paper_id: int, db = None) -> List[Dict]:
    """Get all equations from a paper"""
    result = db.execute(text("""
        SELECT equation_number, latex, context
        FROM paper_equations
        WHERE paper_id = :paper_id
        ORDER BY order_index
    """), {'paper_id': paper_id})
    return [dict(row._mapping) for row in result.fetchall()]


def get_paper_details(paper_id: int, db = None) -> Optional[Dict]:
    """Get paper metadata (title, abstract, authors)"""
    result = db.execute(text("""
        SELECT id, title, abstract, authors, doi, source, publication_date,
               is_processed, section_count, table_count, equation_count
        FROM papers
        WHERE id = :paper_id
    """), {'paper_id': paper_id})
    row = result.fetchone()
    return dict(row._mapping) if row else None


def get_methodology(project_id: int, paper_id: int = None, db = None) -> List[Dict]:
    """Get methodology data for a paper or all papers in project"""
    if paper_id:
        query = """
            SELECT paper_id, methodology_description, custom_attributes
            FROM methodology_data
            WHERE project_id = :project_id AND paper_id = :paper_id
        """
        result = db.execute(text(query), {'project_id': project_id, 'paper_id': paper_id})
    else:
        query = """
            SELECT m.paper_id, p.title, m.methodology_description, m.custom_attributes
            FROM methodology_data m
            JOIN papers p ON p.id = m.paper_id
            WHERE m.project_id = :project_id
        """
        result = db.execute(text(query), {'project_id': project_id})
    
    rows = []
    for row in result.fetchall():
        data = dict(row._mapping)
        # Map DB columns back to expected format
        custom_attrs = data.get('custom_attributes') or {}
        
        rows.append({
            'paper_id': data.get('paper_id'),
            'title': data.get('title'), # Only present in project-wide query
            'methodology_summary': data.get('methodology_description'),
            'data_collection': custom_attrs.get('data_collection'),
            'analysis_methods': custom_attrs.get('analysis_methods'),
            'sample_size': custom_attrs.get('sample_size')
        })
    
    return rows


def get_findings(project_id: int, paper_id: int = None, db = None) -> List[Dict]:
    """Get findings for a paper or all papers in project"""
    if paper_id:
        query = """
            SELECT paper_id, key_finding, limitations, custom_notes
            FROM findings
            WHERE project_id = :project_id AND paper_id = :paper_id
        """
        result = db.execute(text(query), {'project_id': project_id, 'paper_id': paper_id})
    else:
        query = """
            SELECT f.paper_id, p.title, f.key_finding, f.limitations, f.custom_notes
            FROM findings f
            JOIN papers p ON p.id = f.paper_id
            WHERE f.project_id = :project_id
        """
        result = db.execute(text(query), {'project_id': project_id})
    
    return [dict(row._mapping) for row in result.fetchall()]


def get_comparison(project_id: int, db = None) -> Optional[Dict]:
    """Get comparison data for a project"""
    result = db.execute(text("""
        SELECT insights_similarities, insights_differences, selected_paper_ids
        FROM comparison_configs
        WHERE project_id = :project_id
    """), {'project_id': project_id})
    row = result.fetchone()
    return dict(row._mapping) if row else None


def get_synthesis(project_id: int, db = None) -> Optional[Dict]:
    """Get synthesis data for a project"""
    result = db.execute(text("""
        SELECT synthesis_text, key_themes, research_gaps
        FROM synthesis_data
        WHERE project_id = :project_id
    """), {'project_id': project_id})
    row = result.fetchone()
    return dict(row._mapping) if row else None


def get_summary(project_id: int, db = None) -> Optional[Dict]:
    """Get literature review summary for a project"""
    result = db.execute(text("""
        SELECT summary_text, key_insights, methodology_overview,
               main_findings, research_gaps, future_directions, word_count
        FROM project_summaries
        WHERE project_id = :project_id
    """), {'project_id': project_id})
    row = result.fetchone()
    return dict(row._mapping) if row else None


def list_papers_in_library(
    user_id: str, 
    db = None,
    scope: str = 'library',
    selected_paper_ids: List[int] = None
) -> List[Dict]:
    """
    List papers based on scope selection.
    
    Args:
        user_id: User ID
        db: Database session
        scope: 'library' (all papers), 'project' (project papers), or 'selection' (specific papers)
        selected_paper_ids: List of paper IDs when scope is 'selection'
    
    Returns:
        List of paper dicts
    """
    # If user selected specific papers, only return those
    if scope == 'selection' and selected_paper_ids:
        if len(selected_paper_ids) == 1:
            query = """
                SELECT p.id, p.title, p.authors, p.source, p.is_processed,
                       p.section_count, p.table_count
                FROM papers p
                WHERE p.id = :paper_id
            """
            result = db.execute(text(query), {'paper_id': selected_paper_ids[0]})
        else:
            # Build IN clause for multiple IDs
            ids_str = ",".join([str(pid) for pid in selected_paper_ids])
            query = f"""
                SELECT p.id, p.title, p.authors, p.source, p.is_processed,
                       p.section_count, p.table_count
                FROM papers p
                WHERE p.id IN ({ids_str})
            """
            result = db.execute(text(query))
        return [dict(row._mapping) for row in result.fetchall()]
    
    # Default: list all papers in library
    result = db.execute(text("""
        SELECT p.id, p.title, p.authors, p.source, p.is_processed,
               p.section_count, p.table_count
        FROM papers p
        JOIN user_saved_papers usp ON usp.paper_id = p.id
        WHERE usp.user_id = :user_id
        ORDER BY usp.saved_at DESC
        LIMIT 50
    """), {'user_id': user_id})
    return [dict(row._mapping) for row in result.fetchall()]


def list_projects(user_id: str, db = None) -> List[Dict]:
    """List all literature review projects for user"""
    result = db.execute(text("""
        SELECT id, title, description, created_at
        FROM user_literature_reviews
        WHERE user_id = :user_id
        ORDER BY created_at DESC
    """), {'user_id': user_id})
    return [dict(row._mapping) for row in result.fetchall()]


# ==================== WRITE TOOLS ====================

def update_summary(
    user_id: str,
    project_id: int,
    summary_text: Optional[str] = None,
    key_insights: Optional[List[str]] = None,
    methodology_overview: Optional[str] = None,
    main_findings: Optional[str] = None,
    research_gaps: Optional[List[str]] = None,
    future_directions: Optional[str] = None,
    db = None
) -> Dict:
    """Update or create project summary"""
    params = {
        'user_id': user_id,
        'project_id': project_id,
        'summary_text': summary_text,
        'key_insights': key_insights,
        'methodology_overview': methodology_overview,
        'main_findings': main_findings,
        'research_gaps': research_gaps,
        'future_directions': future_directions,
        'word_count': len(summary_text.split()) if summary_text else 0
    }
    
    db.execute(text("""
        INSERT INTO project_summaries 
        (user_id, project_id, summary_text, key_insights, methodology_overview,
         main_findings, research_gaps, future_directions, word_count)
        VALUES (:user_id, :project_id, :summary_text, :key_insights, :methodology_overview,
                :main_findings, :research_gaps, :future_directions, :word_count)
        ON CONFLICT (project_id, user_id) DO UPDATE SET
            summary_text = COALESCE(:summary_text, project_summaries.summary_text),
            key_insights = COALESCE(:key_insights, project_summaries.key_insights),
            methodology_overview = COALESCE(:methodology_overview, project_summaries.methodology_overview),
            main_findings = COALESCE(:main_findings, project_summaries.main_findings),
            research_gaps = COALESCE(:research_gaps, project_summaries.research_gaps),
            future_directions = COALESCE(:future_directions, project_summaries.future_directions),
            word_count = :word_count,
            updated_at = NOW()
    """), params)
    db.commit()
    
    return get_summary(project_id, db) or {}
