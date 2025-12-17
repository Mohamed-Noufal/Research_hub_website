from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.users import get_current_user_id

router = APIRouter()

# ===== Request/Response Models =====

class ColumnConfig(BaseModel):
    id: str
    label: str
    field: str
    type: str  # 'text', 'number', 'select', 'rating'
    width: int
    visible: bool
    order: int
    editable: bool
    isDefault: bool

class TableConfigResponse(BaseModel):
    columns: List[ColumnConfig]
    filters: List[dict]
    sort_config: dict

class TableConfigUpdate(BaseModel):
    columns: Optional[List[ColumnConfig]] = None
    filters: Optional[List[dict]] = None
    sort_config: Optional[dict] = None

class CustomFieldUpdate(BaseModel):
    field_id: str
    value: str

# ===== Default Template =====

DEFAULT_SUMMARY_COLUMNS = [
    {
        "id": "title",
        "label": "Title & Authors",
        "field": "title",
        "type": "text",
        "width": 300,
        "visible": True,
        "order": 0,
        "editable": False,
        "isDefault": True
    },
    {
        "id": "year",
        "label": "Year",
        "field": "year",
        "type": "number",
        "width": 80,
        "visible": True,
        "order": 1,
        "editable": True,
        "isDefault": True
    },
    {
        "id": "methodology",
        "label": "Methodology",
        "field": "methodology",
        "type": "select",
        "width": 150,
        "visible": True,
        "order": 2,
        "editable": True,
        "isDefault": True
    },
    {
        "id": "sample_size",
        "label": "Sample",
        "field": "sampleSize",
        "type": "text",
        "width": 100,
        "visible": True,
        "order": 3,
        "editable": True,
        "isDefault": True
    },
    {
        "id": "key_findings",
        "label": "Key Findings",
        "field": "keyFindings",
        "type": "text",
        "width": 300,
        "visible": True,
        "order": 4,
        "editable": True,
        "isDefault": True
    },
    {
        "id": "quality",
        "label": "Quality",
        "field": "qualityScore",
        "type": "rating",
        "width": 120,
        "visible": True,
        "order": 5,
        "editable": True,
        "isDefault": True
    }
]

# ===== Endpoints =====

@router.get("/projects/{project_id}/tables/{tab_name}/config", response_model=TableConfigResponse)
async def get_table_config(
    project_id: int,
    tab_name: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get table configuration for a specific tab.
    Creates default config if doesn't exist.
    """
    # Check if config exists
    query = """
        SELECT columns, filters, sort_config
        FROM table_configs
        WHERE user_id = :user_id AND project_id = :project_id AND tab_name = :tab_name
    """
    
    result = db.execute(
        text(query),
        {
            "user_id": user_id, 
            "project_id": str(project_id),
            "tab_name": tab_name
        }
    ).fetchone()
    
    if result:
        return TableConfigResponse(
            columns=result[0],
            filters=result[1] or [],
            sort_config=result[2] or {}
        )
    
    # Create default config if doesn't exist
    if tab_name == "summary":
        default_columns = DEFAULT_SUMMARY_COLUMNS
    else:
        default_columns = []
    
    insert_query = """
        INSERT INTO table_configs (user_id, project_id, tab_name, columns, filters, sort_config)
        VALUES (:user_id, :project_id, :tab_name, :columns::jsonb, '[]'::jsonb, '{}'::jsonb)
        RETURNING columns, filters, sort_config
    """
    
    result = db.execute(
        text(insert_query),
        {
            "user_id": user_id,
            "project_id": str(project_id),
            "tab_name": tab_name,
            "columns": str(default_columns).replace("'", '"')
        }
    ).fetchone()
    
    db.commit()
    
    return TableConfigResponse(
        columns=default_columns,
        filters=[],
        sort_config={}
    )


@router.put("/projects/{project_id}/tables/{tab_name}/config", response_model=TableConfigResponse)
async def update_table_config(
    project_id: int,
    tab_name: str,
    config: TableConfigUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update table configuration."""
    
    # Build update query dynamically based on provided fields
    update_parts = []
    params = {
        "user_id": user_id,
        "project_id": str(project_id),
        "tab_name": tab_name
    }
    
    if config.columns is not None:
        update_parts.append("columns = :columns::jsonb")
        params["columns"] = str([col.dict() for col in config.columns]).replace("'", '"')
    
    if config.filters is not None:
        update_parts.append("filters = :filters::jsonb")
        params["filters"] = str(config.filters).replace("'", '"')
    
    if config.sort_config is not None:
        update_parts.append("sort_config = :sort_config::jsonb")
        params["sort_config"] = str(config.sort_config).replace("'", '"')
    
    if not update_parts:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    query = f"""
        UPDATE table_configs
        SET {', '.join(update_parts)}
        WHERE user_id = :user_id AND project_id = :project_id AND tab_name = :tab_name
        RETURNING columns, filters, sort_config
    """
    
    result = db.execute(text(query), params).fetchone()
    db.commit()
    
    if not result:
        raise HTTPException(status_code=404, detail="Table config not found")
    
    return {"message": "Config updated successfully"}


@router.patch("/projects/{project_id}/papers/{paper_id}/custom-fields")
async def update_custom_field(
    project_id: int,
    paper_id: int,
    field_update: CustomFieldUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update or create a custom field value for a paper."""
    
    query = """
        INSERT INTO custom_field_values (user_id, project_id, paper_id, field_id, value)
        VALUES (:user_id, :project_id, :paper_id, :field_id, :value)
        ON CONFLICT (user_id, project_id, paper_id, field_id)
        DO UPDATE SET value = :value, updated_at = NOW()
        RETURNING id
    """
    
    result = db.execute(
        text(query),
        {
            "user_id": user_id,
            "project_id": str(project_id),
            "paper_id": str(paper_id),
            "field_id": field_update.field_id,
            "value": field_update.value
        }
    ).fetchone()
    
    db.commit()
    
    return {"message": "Custom field updated successfully", "id": result[0]}


@router.get("/projects/{project_id}/papers")
async def get_project_papers(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all papers in a project with enriched data.
    Joins with methodology_data and findings tables.
    """
    
    # We must cast user_id to text for the join if the tables use text user_ids (which they do currently)
    # The IDs in findings/methodology tables are stored as strings based on seed function.
    
    query = """
        SELECT 
            p.*,
            -- Methodology Data
            md.methodology_description as "methodologyDescription",
            md.methodology_context as "methodologyContext",
            md.approach_novelty as "approachNovelty",
            -- Findings Data
            f.key_finding as "keyFindings",
            f.limitations as "limitations",
            -- Custom Fields
            COALESCE(
                json_object_agg(cfv.field_id, cfv.value) FILTER (WHERE cfv.field_id IS NOT NULL),
                '{}'::json
            ) as custom_fields
        FROM papers p
        INNER JOIN project_papers pp ON p.id = pp.paper_id
        -- Join Methodology
        LEFT JOIN methodology_data md ON (
            md.paper_id = p.id
            AND md.user_id = :user_id 
            AND md.project_id = :project_id
        )
        -- Join Findings
        LEFT JOIN findings f ON (
            f.paper_id = p.id
            AND f.user_id = :user_id 
            AND f.project_id = :project_id
        )
        -- Join Custom Fields
        LEFT JOIN custom_field_values cfv ON p.id = cfv.paper_id 
            AND cfv.user_id = :user_id 
            AND cfv.project_id = :project_id
        WHERE pp.project_id = :project_id
        GROUP BY 
            p.id, p.title, p.publication_date,
            md.methodology_description, md.methodology_context, md.approach_novelty,
            f.key_finding, f.limitations
        ORDER BY p.publication_date DESC, p.title ASC
    """
    
    try:
        results = db.execute(
            text(query),
            {
                "user_id": user_id,
                "project_id": str(project_id)
            }
        ).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Query Error: {str(e)}")
    
    papers = []
    for row in results:
        paper_dict = dict(row._mapping)
        
        # Ensure year is int if present
        if paper_dict.get('publication_date'):
            try:
                # Extract year from date if needed, though 'year' might be a column in p.*
                # Checking Paper model: it has publication_date (DateTime). 
                # Does it have 'year'? No.
                # Frontend expects 'year'.
                # Let's derive it.
                dt = paper_dict['publication_date']
                if dt:
                    paper_dict['year'] = dt.year
            except:
                pass
        
        # Fallback for year if not computed
        if 'year' not in paper_dict or not paper_dict['year']:
             paper_dict['year'] = 2023 # fallback
             
        papers.append(paper_dict)
    
    return {"papers": papers}
