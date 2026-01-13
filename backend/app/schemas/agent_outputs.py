"""
Pydantic Output Schemas for AI Agent
These schemas ensure LLM output matches database structure exactly.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ==================== METHODOLOGY OUTPUT ====================

class MethodologyOutput(BaseModel):
    """Schema matching methodology_data table"""
    
    methodology_summary: str = Field(
        ..., 
        min_length=10,
        description="Brief overview of the research methodology"
    )
    data_collection: Optional[str] = Field(
        None,
        description="How data was collected (surveys, experiments, etc.)"
    )
    analysis_methods: Optional[str] = Field(
        None,
        description="Analysis techniques used (statistical, qualitative, etc.)"
    )
    sample_size: Optional[str] = Field(
        None,
        description="Sample size and population details"
    )
    methodology_context: Optional[str] = Field(
        None,
        description="Previous context or related approaches"
    )
    approach_novelty: Optional[str] = Field(
        None,
        description="What makes this approach different or novel"
    )
    
    @field_validator('methodology_summary')
    @classmethod
    def summary_not_placeholder(cls, v):
        if v.lower().startswith(('todo', 'placeholder', 'fill in')):
            raise ValueError('Summary cannot be a placeholder')
        return v


# ==================== FINDINGS OUTPUT ====================

class FindingsOutput(BaseModel):
    """Schema matching findings table"""
    
    key_finding: str = Field(
        ...,
        min_length=10,
        description="The main finding or result from the paper"
    )
    limitations: Optional[str] = Field(
        None,
        description="Limitations or constraints of the research"
    )
    custom_notes: Optional[str] = Field(
        None,
        description="Additional notes or observations"
    )
    evidence_level: Optional[str] = Field(
        None,
        description="Strength of evidence: 'strong', 'moderate', 'weak'"
    )
    
    @field_validator('evidence_level')
    @classmethod
    def valid_evidence_level(cls, v):
        if v is not None and v.lower() not in ('strong', 'moderate', 'weak'):
            raise ValueError("evidence_level must be 'strong', 'moderate', or 'weak'")
        return v.lower() if v else None


# ==================== COMPARISON OUTPUT ====================

class ComparisonOutput(BaseModel):
    """Schema matching comparison_configs table"""
    
    insights_similarities: str = Field(
        ...,
        min_length=10,
        description="What the compared papers have in common"
    )
    insights_differences: str = Field(
        ...,
        min_length=10,
        description="How the compared papers differ"
    )
    comparison_summary: Optional[str] = Field(
        None,
        description="Overall summary of the comparison"
    )


# ==================== SYNTHESIS OUTPUT ====================

class SynthesisOutput(BaseModel):
    """Schema matching synthesis table structure"""
    
    synthesis_text: Optional[str] = Field(
        None,
        description="Overall synthesis narrative"
    )
    key_themes: Optional[List[str]] = Field(
        default_factory=list,
        description="Major themes identified across papers"
    )
    research_gaps: Optional[List[str]] = Field(
        default_factory=list,
        description="Gaps in the literature that need addressing"
    )
    theme_strength: Optional[str] = Field(
        None,
        description="Overall strength of themes: 'strong', 'moderate', 'weak'"
    )


# ==================== SUMMARY OUTPUT ====================

class SummaryOutput(BaseModel):
    """Schema matching project_summaries table"""
    
    summary_text: str = Field(
        ...,
        min_length=50,
        description="Comprehensive literature review summary"
    )
    key_insights: Optional[List[str]] = Field(
        default_factory=list,
        description="Key insights from the review"
    )
    methodology_overview: Optional[str] = Field(
        None,
        description="Overview of methodologies used across papers"
    )
    main_findings: Optional[str] = Field(
        None,
        description="Summary of main findings"
    )
    research_gaps: Optional[List[str]] = Field(
        default_factory=list,
        description="Identified research gaps"
    )
    future_directions: Optional[str] = Field(
        None,
        description="Suggested future research directions"
    )


# ==================== TASK STATE OUTPUT ====================

class TaskStateOutput(BaseModel):
    """Schema for task state updates"""
    
    task_id: str
    status: str = Field(..., pattern='^(pending|running|completed|failed|paused)$')
    current_phase: Optional[str] = None
    total_items: int = 0
    processed_items: int = 0
    completed_item_ids: List[int] = Field(default_factory=list)
    failed_item_ids: List[int] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    @property
    def progress_percentage(self) -> int:
        if self.total_items == 0:
            return 0
        return int((self.processed_items / self.total_items) * 100)


# ==================== MEMORY OUTPUT ====================

class MemoryOutput(BaseModel):
    """Schema for extracted memories"""
    
    memory_text: str = Field(
        ...,
        min_length=5,
        description="The memory fact to store"
    )
    memory_type: str = Field(
        default='semantic',
        pattern='^(semantic|episodic|preference|project)$'
    )
    category: Optional[str] = Field(
        None,
        description="Category like 'research_focus', 'paper_preference'"
    )
    importance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance from 0 to 1"
    )


class ExtractedMemories(BaseModel):
    """Multiple memories extracted from a conversation"""
    
    memories: List[MemoryOutput] = Field(
        default_factory=list,
        max_length=5,  # Max 5 memories per extraction
        description="List of extracted memory facts"
    )


# ==================== VALIDATION HELPERS ====================

def validate_and_parse(raw_json: str, schema_class: type[BaseModel]) -> BaseModel:
    """
    Parse LLM output and validate against schema.
    Raises ValidationError if invalid.
    """
    import json
    
    # Clean common LLM output issues
    cleaned = raw_json.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    if cleaned.startswith('```'):
        cleaned = cleaned[3:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    # Parse and validate
    data = json.loads(cleaned)
    return schema_class.model_validate(data)


def get_schema_prompt(schema_class: type[BaseModel]) -> str:
    """
    Generate a prompt-friendly schema description for LLM.
    """
    schema = schema_class.model_json_schema()
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    lines = ["Return JSON matching this schema:"]
    lines.append("{")
    
    for name, prop in properties.items():
        req = "(required)" if name in required else "(optional)"
        desc = prop.get('description', '')
        lines.append(f'  "{name}": "{desc}" {req},')
    
    lines.append("}")
    return "\n".join(lines)
