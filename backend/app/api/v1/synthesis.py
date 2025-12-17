"""
API endpoints for Synthesis tab data management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.users import get_current_user_id

router = APIRouter()


# Request/Response Models
class ColumnDef(BaseModel):
    id: str
    title: str


class RowDef(BaseModel):
    id: str
    label: str


class SynthesisStructure(BaseModel):
    columns: List[ColumnDef]
    rows: List[RowDef]


class CellUpdate(BaseModel):
    row_id: str
    column_id: str
    value: str


# ===== SYNTHESIS ENDPOINTS =====

@router.get("/projects/{project_id}/synthesis")
async def get_synthesis_data(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get synthesis table structure and all cell values"""
    
    # Get structure
    structure_query = """
        SELECT columns, rows
        FROM synthesis_configs
        WHERE user_id = :user_id AND project_id = :project_id
    """
    
    structure = db.execute(
        text(structure_query),
        {"user_id": user_id, "project_id": project_id}
    ).fetchone()
    
    # Get all cells
    cells_query = """
        SELECT row_id, column_id, value
        FROM synthesis_cells
        WHERE user_id = :user_id AND project_id = :project_id
    """
    
    cells_result = db.execute(
        text(cells_query),
        {"user_id": user_id, "project_id": project_id}
    ).fetchall()
    
    # Build cells dict
    cells = {}
    for row in cells_result:
        key = f"{row.row_id}_{row.column_id}"
        cells[key] = row.value or ""
    
    if structure:
        return {
            "columns": structure.columns or [],
            "rows": structure.rows or [],
            "cells": cells
        }
    
    # Return default structure
    return {
        "columns": [
            {"id": "col1", "title": "Theme 1: Effectiveness"},
            {"id": "col2", "title": "Theme 2: Implementation"},
            {"id": "col3", "title": "Theme 3: Limitations"}
        ],
        "rows": [],
        "cells": {}
    }


@router.put("/projects/{project_id}/synthesis/structure")
async def update_synthesis_structure(
    project_id: int,
    structure: SynthesisStructure,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update synthesis table structure"""
    
    # Check if config exists
    check_query = """
        SELECT id FROM synthesis_configs
        WHERE user_id = :user_id AND project_id = :project_id
    """
    
    existing = db.execute(
        text(check_query),
        {"user_id": user_id, "project_id": project_id}
    ).fetchone()
    
    # Convert to JSON
    import json
    columns_json = json.dumps([col.dict() for col in structure.columns])
    rows_json = json.dumps([row.dict() for row in structure.rows])
    
    if existing:
        # Update
        query = """
            UPDATE synthesis_configs
            SET columns = :columns, rows = :rows
            WHERE user_id = :user_id AND project_id = :project_id
        """
    else:
        # Insert
        query = """
            INSERT INTO synthesis_configs (user_id, project_id, columns, rows)
            VALUES (:user_id, :project_id, :columns, :rows)
        """
    
    db.execute(text(query), {
        "user_id": user_id,
        "project_id": project_id,
        "columns": columns_json,
        "rows": rows_json
    })
    db.commit()
    
    return {"message": "Structure updated successfully"}


@router.patch("/projects/{project_id}/synthesis/cells")
async def update_synthesis_cell(
    project_id: int,
    cell: CellUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update a synthesis cell value"""
    
    # Check if cell exists
    check_query = """
        SELECT id FROM synthesis_cells
        WHERE user_id = :user_id 
        AND project_id = :project_id 
        AND row_id = :row_id
        AND column_id = :column_id
    """
    
    existing = db.execute(text(check_query), {
        "user_id": user_id,
        "project_id": project_id,
        "row_id": cell.row_id,
        "column_id": cell.column_id
    }).fetchone()
    
    if existing:
        # Update
        query = """
            UPDATE synthesis_cells
            SET value = :value
            WHERE user_id = :user_id 
            AND project_id = :project_id 
            AND row_id = :row_id
            AND column_id = :column_id
        """
    else:
        # Insert
        query = """
            INSERT INTO synthesis_cells (user_id, project_id, row_id, column_id, value)
            VALUES (:user_id, :project_id, :row_id, :column_id, :value)
        """
    
    db.execute(text(query), {
        "user_id": user_id,
        "project_id": project_id,
        "row_id": cell.row_id,
        "column_id": cell.column_id,
        "value": cell.value
    })
    db.commit()
    
    return {"message": "Cell updated successfully"}
