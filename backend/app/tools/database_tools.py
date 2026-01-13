"""
Database tools for existing tables
Integrates with projects, papers, findings, comparison_configs, etc.

NOTE: All functions are SYNC because the orchestrator passes a sync Session.
"""
from sqlalchemy import text
from typing import List, Dict, Optional
from difflib import SequenceMatcher

# ==================== PROJECT TOOLS ====================

def get_project_by_name(
    project_name: str,
    user_id: str,
    db,
    fuzzy: bool = True
) -> Optional[Dict]:
    """
    Find project by name (supports fuzzy matching)
    """
    # Get all user projects
    result = db.execute(
        text("""
            SELECT id, title, description, created_at
            FROM user_literature_reviews
            WHERE user_id = :user_id
        """),
        {'user_id': user_id}
    )
    
    projects = [dict(row._mapping) for row in result.fetchall()]
    
    if not projects:
        return None
    
    # Exact match first
    for project in projects:
        if project['title'].lower() == project_name.lower():
            return project
    
    # Fuzzy match if enabled
    if fuzzy:
        best_match = None
        best_score = 0.6  # Minimum similarity threshold
        
        for project in projects:
            score = SequenceMatcher(None, project_name.lower(), project['title'].lower()).ratio()
            if score > best_score:
                best_score = score
                best_match = project
        
        return best_match
    
    return None

def get_project_papers(
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
                p.publication_date,
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
    
    result = db.execute(
        text(query),
        {'project_id': project_id}
    )
    
    return [dict(row._mapping) for row in result.fetchall()]

def link_paper_to_project(
    project_id: int,
    paper_id: int,
    db = None
) -> Dict:
    """
    Add paper to project in project_papers table
    """
    db.execute(
        text("""
            INSERT INTO project_papers (project_id, paper_id)
            VALUES (:project_id, :paper_id)
            ON CONFLICT (project_id, paper_id) DO NOTHING
        """),
        {'project_id': project_id, 'paper_id': paper_id}
    )
    db.commit()
    
    return {
        'project_id': project_id,
        'paper_id': paper_id,
        'status': 'linked'
    }

# ==================== COMPARISON TOOLS ====================

def update_comparison(
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
        'project_id': project_id,
        'similarities': similarities,
        'differences': differences,
        'selected_papers': selected_papers
    }
    
    if similarities is not None:
        updates.append("insights_similarities = :similarities")
    
    if differences is not None:
        updates.append("insights_differences = :differences")
    
    if selected_papers is not None:
        updates.append("selected_paper_ids = :selected_papers")
    
    if updates:
        # Upsert into comparison_configs table
        db.execute(
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
        db.commit()
    
    # Return updated config
    result = db.execute(
        text("""
            SELECT * FROM comparison_configs
            WHERE user_id = :user_id AND project_id = :project_id
        """),
        {'user_id': user_id, 'project_id': project_id}
    )
    
    row = result.fetchone()
    return dict(row._mapping) if row else {}

# ==================== FINDINGS TOOLS ====================

def update_findings(
    user_id: str,
    project_id: int,
    paper_id: int,
    key_finding: Optional[str] = None,
    limitations: Optional[str] = None,
    custom_notes: Optional[str] = None,
    evidence_level: Optional[str] = None,
    db = None
) -> Dict:
    """
    Update findings table with Pydantic validation and history logging.
    """
    from app.schemas.agent_outputs import FindingsOutput
    
    # Validate input with Pydantic
    try:
        validated = FindingsOutput(
            key_finding=key_finding or "Not provided",
            limitations=limitations,
            custom_notes=custom_notes,
            evidence_level=evidence_level
        )
    except Exception as e:
        return {"error": f"Validation failed: {str(e)}", "success": False}
    
    params = {
        'user_id': user_id,
        'project_id': project_id,
        'paper_id': paper_id,
        'key_finding': validated.key_finding,
        'limitations': validated.limitations,
        'custom_notes': validated.custom_notes
    }
    
    # Get old data for history
    old_result = db.execute(
        text("""
            SELECT * FROM findings
            WHERE user_id = :user_id AND project_id = :project_id AND paper_id = :paper_id
        """),
        params
    )
    old_row = old_result.fetchone()
    old_data = dict(old_row._mapping) if old_row else None
    record_id = old_data.get('id') if old_data else None
    
    # Build update fields
    updates = []
    if validated.key_finding is not None:
        updates.append("key_finding = :key_finding")
    if validated.limitations is not None:
        updates.append("limitations = :limitations")
    if validated.custom_notes is not None:
        updates.append("custom_notes = :custom_notes")
    
    if updates:
        # Upsert into findings table
        db.execute(
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
        db.commit()
        
        # Log to history
        try:
            import json
            db.execute(
                text("""
                    INSERT INTO data_change_history 
                    (user_id, table_name, record_id, operation, old_data, new_data, changed_by)
                    VALUES (:user_id, 'findings', :record_id, :operation, :old_data, :new_data, 'agent')
                """),
                {
                    'user_id': user_id,
                    'record_id': record_id or '00000000-0000-0000-0000-000000000000',
                    'operation': 'UPDATE' if old_data else 'INSERT',
                    'old_data': json.dumps(old_data) if old_data else None,
                    'new_data': json.dumps(validated.model_dump())
                }
            )
            db.commit()
        except Exception:
            pass  # Don't fail on history logging errors
    
    # Return updated finding
    result = db.execute(
        text("""
            SELECT * FROM findings
            WHERE user_id = :user_id AND project_id = :project_id AND paper_id = :paper_id
        """),
        params
    )
    
    row = result.fetchone()
    return dict(row._mapping) if row else {}

# ==================== METHODOLOGY TOOLS ====================

def update_methodology(
    user_id: str,
    project_id: int,
    paper_id: int,
    methodology_summary: Optional[str] = None,
    data_collection: Optional[str] = None,
    analysis_methods: Optional[str] = None,
    sample_size: Optional[str] = None,
    methodology_context: Optional[str] = None,
    approach_novelty: Optional[str] = None,
    db = None
) -> Dict:
    """
    Update methodology_data table with Pydantic validation and history logging.
    """
    from app.schemas.agent_outputs import MethodologyOutput
    
    # Validate input with Pydantic
    try:
        validated = MethodologyOutput(
            methodology_summary=methodology_summary or "Not provided",
            data_collection=data_collection,
            analysis_methods=analysis_methods,
            sample_size=sample_size,
            methodology_context=methodology_context,
            approach_novelty=approach_novelty
        )
    except Exception as e:
        return {"error": f"Validation failed: {str(e)}", "success": False}
    
    params = {
        'user_id': user_id,
        'project_id': project_id,
        'paper_id': paper_id,
        'methodology_summary': validated.methodology_summary,
        'data_collection': validated.data_collection,
        'analysis_methods': validated.analysis_methods,
        'sample_size': validated.sample_size,
        'methodology_context': validated.methodology_context,
        'approach_novelty': validated.approach_novelty
    }
    
    # Get old data for history
    old_result = db.execute(
        text("""
            SELECT * FROM methodology_data
            WHERE user_id = :user_id AND project_id = :project_id AND paper_id = :paper_id
        """),
        params
    )
    old_row = old_result.fetchone()
    old_data = dict(old_row._mapping) if old_row else None
    record_id = old_data.get('id') if old_data else None
    
    # Build update fields
    updates = []
    
    # Store additional fields in custom_attributes
    custom_attrs = old_data.get('custom_attributes', {}) if old_data else {}
    if validated.data_collection:
        custom_attrs['data_collection'] = validated.data_collection
    if validated.analysis_methods:
        custom_attrs['analysis_methods'] = validated.analysis_methods
    if validated.sample_size:
        custom_attrs['sample_size'] = validated.sample_size
        
    import json
    # Map methodology_summary (Pydantic) -> methodology_description (DB)
    if validated.methodology_summary is not None:
        updates.append("methodology_description = :methodology_summary")
    
    # Save methodology_context and approach_novelty to their proper columns
    if validated.methodology_context is not None:
        updates.append("methodology_context = :methodology_context")
    if validated.approach_novelty is not None:
        updates.append("approach_novelty = :approach_novelty")
    
    # Always update custom_attributes if we have any
    updates.append("custom_attributes = :custom_attributes")
    
    # Add custom attributes to params
    params['custom_attributes'] = json.dumps(custom_attrs)
    
    if updates:
        # Upsert into methodology_data table
        # Note: mapping methodology_summary to methodology_description column
        # and others to custom_attributes JSONB
        db.execute(
            text(f"""
                INSERT INTO methodology_data 
                (user_id, project_id, paper_id, methodology_description, methodology_context, approach_novelty, custom_attributes)
                VALUES (:user_id, :project_id, :paper_id, :methodology_summary, :methodology_context, :approach_novelty, :custom_attributes)
                ON CONFLICT (user_id, project_id, paper_id) DO UPDATE SET
                    {', '.join(updates)},
                    updated_at = NOW()
            """),
            params
        )
        db.commit()
        
        # Log to history
        try:
            db.execute(
                text("""
                    INSERT INTO data_change_history 
                    (user_id, table_name, record_id, operation, old_data, new_data, changed_by)
                    VALUES (:user_id, 'methodology_data', :record_id, :operation, :old_data, :new_data, 'agent')
                """),
                {
                    'user_id': user_id,
                    'record_id': record_id or '00000000-0000-0000-0000-000000000000',
                    'operation': 'UPDATE' if old_data else 'INSERT',
                    'old_data': json.dumps(old_data, default=str) if old_data else None,
                    'new_data': json.dumps(validated.model_dump(), default=str)
                }
            )
            db.commit()
        except Exception:
            pass  # Don't fail on history logging errors
    
    # Return updated methodology
    result = db.execute(
        text("""
            SELECT * FROM methodology_data
            WHERE user_id = :user_id AND project_id = :project_id AND paper_id = :paper_id
        """),
        params
    )
    
    row = result.fetchone()
    return dict(row._mapping) if row else {}

# ==================== SYNTHESIS TOOLS ====================

def update_synthesis(
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
    
    db.execute(
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
    db.commit()
    
    # Return updated synthesis
    result = db.execute(
        text("""
            SELECT * FROM synthesis_data
            WHERE user_id = :user_id AND project_id = :project_id
        """),
        {'user_id': user_id, 'project_id': project_id}
    )
    
    row = result.fetchone()
    return dict(row._mapping) if row else {}
