"""
Database tools for existing tables
Integrates with projects, papers, findings, comparison_configs, etc.
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
    Get all papers in a project from project_papers table
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
                pp.added_at,
                p.is_processed
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

async def link_paper_to_project(
    project_id: int,
    paper_id: int,
    db = None
) -> Dict:
    """
    Add paper to project in project_papers table
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
    Update comparison_configs table with insights
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
    
    # Note: selected_paper_ids usually requires handling array/list serialization depending on DB driver
    # Assuming list[int] works with the driver or wrapping related handling might be needed.
    if selected_papers is not None:
        updates.append("selected_paper_ids = :selected_papers")
        params['selected_papers'] = selected_papers
    
    if not updates:
        # If no updates, just return existing
        pass 
    else:
        # Upsert into comparison_configs table
        # Note: 'insights_similarities' and 'insights_differences' columns assumed to exist
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
    
    row = result.fetchone()
    return dict(row._mapping) if row else {}

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
    Update findings table
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
    
    if updates:
        # Upsert into findings table
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
    
    row = result.fetchone()
    return dict(row._mapping) if row else {}

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
    Update methodology_data table
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
    
    if updates:
        # Upsert into methodology_data table
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
    
    row = result.fetchone()
    return dict(row._mapping) if row else {}

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
    Update synthesis_data table
    """
    params = {
        'user_id': user_id,
        'project_id': project_id,
        'synthesis_text': synthesis_text,
        'key_themes': key_themes,
        'research_gaps': research_gaps
    }
    
    # Upsert into synthesis_data table
    # Using COALESCE to keep existing values if input is None (unless strict overwrite wanted)
    # The SQL below handles nullable params - if python param is None, we should handle it.
    # Actually simpler: Only update provided fields. Or standard upsert.
    # Let's use standard upsert logic but handle Nones carefully in SQL query:
    
    # If synthesis_text is None, don't update it?
    # Actually for synthesis, usually we rewrite the whole blocking chunk.
    # The provided SQL in Phase 3 doc does COALESCE with the *table column*.
    
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
    
    row = result.fetchone()
    return dict(row._mapping) if row else {}
