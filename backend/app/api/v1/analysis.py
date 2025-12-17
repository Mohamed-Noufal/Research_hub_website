"""
API endpoints for Analysis & Visuals tab
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.users import get_current_user_id

router = APIRouter()


# Request/Response Models
class ChartPreferences(BaseModel):
    chart_preferences: Dict[str, Any]

class AnalysisConfigUpdate(BaseModel):
    chart_preferences: Dict[str, Any]


# ===== ANALYSIS ENDPOINTS =====

@router.get("/projects/{project_id}/analysis/config")
async def get_analysis_config(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get analysis data and chart preferences"""
    
    # Get chart preferences
    query = """
        SELECT chart_preferences, custom_metrics
        FROM analysis_configs
        WHERE user_id = :user_id AND project_id = :project_id
    """
    
    result = db.execute(
        text(query),
        {"user_id": user_id, "project_id": project_id}
    ).fetchone()
    
    if result:
        return {
            "chart_preferences": result.chart_preferences or {},
            "custom_metrics": result.custom_metrics or []
        }
    
    # Return defaults
    return {
        "chart_preferences": {
            "methodology_chart_type": "pie",
            "timeline_chart_type": "bar",
            "show_quality_cards": True,
            "color_scheme": "default"
        },
        "custom_metrics": []
    }


@router.put("/projects/{project_id}/analysis/config")
async def update_analysis_config(
    project_id: int,
    config: AnalysisConfigUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update analysis chart preferences"""
    
    # Check if config exists
    check_query = """
        SELECT id FROM analysis_configs
        WHERE user_id = :user_id AND project_id = :project_id
    """
    
    existing = db.execute(
        check_query,
        {"user_id": user_id, "project_id": project_id}
    ).fetchone()
    
    import json
    prefs_json = json.dumps(config.chart_preferences)
    
    if existing:
        # Update
        query = """
            UPDATE analysis_configs
            SET chart_preferences = :chart_preferences
            WHERE user_id = :user_id AND project_id = :project_id
        """
    else:
        # Insert
        query = """
            INSERT INTO analysis_configs (user_id, project_id, chart_preferences)
            VALUES (:user_id, :project_id, :chart_preferences)
        """
    
    db.execute(query, {
        "user_id": user_id,
        "project_id": project_id,
        "chart_preferences": prefs_json
    })
    db.commit()
    
    return {"message": "Preferences updated successfully"}
