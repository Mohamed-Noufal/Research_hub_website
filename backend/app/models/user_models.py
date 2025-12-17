"""
User Data Models for ResearchHub
Handles user-specific research data without full authentication
"""

import uuid
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from app.core.database import Base

class LocalUser(Base):
    """Local user for research platform (no authentication required)"""
    __tablename__ = "local_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    device_info = Column(JSON, nullable=True)  # Browser/device info

    # Relationships
    saved_papers = relationship("UserSavedPaper", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("UserNote", back_populates="user", cascade="all, delete-orphan")
    literature_reviews = relationship("UserLiteratureReview", back_populates="user", cascade="all, delete-orphan")
    uploads = relationship("UserUpload", back_populates="user", cascade="all, delete-orphan")
    search_history = relationship("UserSearchHistory", back_populates="user", cascade="all, delete-orphan")

class UserSavedPaper(Base):
    """User's saved papers with personal metadata"""
    __tablename__ = "user_saved_papers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(ARRAY(String), default=list)  # User-defined tags
    personal_notes = Column(Text, nullable=True)  # Quick notes
    read_status = Column(String(20), default="unread")  # unread, reading, read
    rating = Column(Integer, nullable=True)  # 1-5 stars

    # Relationships
    user = relationship("LocalUser", back_populates="saved_papers")
    paper = relationship("Paper")

class UserNote(Base):
    """User's research notes with folder hierarchy"""
    __tablename__ = "user_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=True)  # Can be general notes
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)  # Can be empty for folders
    content_type = Column(String(50), default="markdown")  # markdown, html, plain

    # Folder hierarchy fields
    parent_id = Column(Integer, ForeignKey("user_notes.id"), nullable=True)  # Parent folder ID
    path = Column(String(1000), nullable=True)  # Path for fast queries (e.g., "/root/personal/research")
    is_folder = Column(Boolean, default=False)  # True for folders, False for notes
    level = Column(Integer, default=0)  # Depth level (0 = root, 1 = child, etc.)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("LocalUser", back_populates="notes")
    paper = relationship("Paper")
    parent = relationship("UserNote", remote_side=[id], backref="children")

class UserLiteratureReview(Base):
    """User's literature review projects"""
    __tablename__ = "user_literature_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    paper_ids = Column(ARRAY(Integer), default=list)  # IDs of papers in this review
    status = Column(String(50), default="draft")  # draft, active, completed, archived
    review_metadata = Column(JSON, default=dict)  # Additional metadata storage
    export_data = Column(JSON, default=dict)  # Export configuration and history
    ai_features_enabled = Column(Boolean, default=False)  # Enable AI features
    advanced_analytics = Column(JSON, default=dict)  # Advanced analytics configuration
    custom_views = Column(JSON, default=dict)  # Custom view configurations
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("LocalUser", back_populates="literature_reviews")
    annotations = relationship("LiteratureReviewAnnotation", back_populates="review", cascade="all, delete-orphan")
    findings = relationship("LiteratureReviewFinding", back_populates="review", cascade="all, delete-orphan")
    comparisons = relationship("PaperComparison", back_populates="project", cascade="all, delete-orphan")
    citation_formats = relationship("CitationFormat", back_populates="project", cascade="all, delete-orphan")
    research_themes = relationship("ResearchTheme", back_populates="project", cascade="all, delete-orphan")

class LiteratureReviewAnnotation(Base):
    """Paper annotations for literature reviews"""
    __tablename__ = "literature_review_annotations"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    methodology = Column(String(100), nullable=True)  # experimental, survey, case-study, meta-analysis, review, other
    sample_size = Column(String(255), nullable=True)
    key_findings = Column(JSON, default=list)  # Array of findings
    limitations = Column(JSON, default=list)  # Array of limitations
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    review = relationship("UserLiteratureReview", back_populates="annotations")
    paper = relationship("Paper")

class LiteratureReviewFinding(Base):
    """Research findings for literature reviews"""
    __tablename__ = "literature_review_findings"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    description = Column(Text, nullable=False)
    supporting_papers = Column(ARRAY(Integer), default=list)  # Array of paper IDs
    finding_type = Column(String(50), nullable=True)  # positive, negative, neutral
    evidence_level = Column(String(50), nullable=True)  # strong, moderate, weak
    citation_count = Column(Integer, default=0)  # Number of citations referencing this finding
    methodology_match = Column(JSON, nullable=True)  # Methodology match data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    review = relationship("UserLiteratureReview", back_populates="findings")

# Phase 2: Research Analysis Models

class PaperComparison(Base):
    """Paper comparison data for literature reviews"""
    __tablename__ = "paper_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    paper_ids = Column(ARRAY(Integer), nullable=False)  # Papers being compared
    comparison_data = Column(JSON, nullable=True)  # Methodology, sample, results comparison
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("UserLiteratureReview", back_populates="comparisons")

class CitationFormat(Base):
    """Citation templates and formatting"""
    __tablename__ = "citation_formats"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    format_type = Column(String(50), nullable=False)  # 'APA', 'MLA', 'Chicago', 'Harvard'
    custom_template = Column(Text, nullable=True)  # Optional custom format
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("UserLiteratureReview", back_populates="citation_formats")

class ResearchTheme(Base):
    """Research themes for analysis"""
    __tablename__ = "research_themes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    theme_name = Column(String(255), nullable=False)
    theme_description = Column(Text, nullable=True)
    supporting_findings = Column(ARRAY(Integer), default=list)  # Array of finding IDs
    paper_count = Column(Integer, default=0)
    theme_strength = Column(String(50), nullable=True)  # strong, moderate, weak
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("UserLiteratureReview", back_populates="research_themes")

# Phase 3: Advanced Features Models

class SpreadsheetTemplate(Base):
    """Excel-like spreadsheet templates for literature reviews"""
    __tablename__ = "spreadsheet_templates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    template_name = Column(String(255), nullable=False)
    template_config = Column(JSON, nullable=True)  # Column definitions, cell types, validation rules
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("UserLiteratureReview")
    data_rows = relationship("SpreadsheetData", back_populates="template", cascade="all, delete-orphan")

class SpreadsheetData(Base):
    """Spreadsheet data storage"""
    __tablename__ = "spreadsheet_data"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("spreadsheet_templates.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    row_data = Column(JSON, nullable=False)  # Individual row data
    cell_data = Column(JSON, nullable=True)  # Individual cell configurations
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    template = relationship("SpreadsheetTemplate", back_populates="data_rows")
    project = relationship("UserLiteratureReview")

class AISynthesis(Base):
    """AI synthesis and reporting"""
    __tablename__ = "ai_synthesis"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    synthesis_type = Column(String(50), nullable=False)  # 'summary', 'comparison', 'theme_analysis', 'methodology', 'gap_analysis'
    input_data = Column(JSON, nullable=True)  # Data used for synthesis
    ai_prompt = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)
    confidence_score = Column(Integer, nullable=True)  # Confidence score (0-100)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("UserLiteratureReview")

class ExportConfiguration(Base):
    """Export configurations for literature reviews"""
    __tablename__ = "export_configurations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    export_type = Column(String(50), nullable=False)  # 'word', 'excel', 'pdf', 'csv'
    template_name = Column(String(255), nullable=True)
    configuration = Column(JSON, nullable=True)  # Format-specific configuration
    output_path = Column(String(500), nullable=True)  # Generated file path
    status = Column(String(50), default="draft")  # draft, generating, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("UserLiteratureReview")

class AnalysisTemplate(Base):
    """Custom analysis templates"""
    __tablename__ = "analysis_templates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("user_literature_reviews.id"), nullable=False)
    template_type = Column(String(50), nullable=False)  # 'comparison_matrix', 'evidence_table', 'methodology_table'
    template_config = Column(JSON, nullable=False)
    custom_fields = Column(JSON, nullable=True)  # Additional fields beyond standard
    is_public = Column(Boolean, default=False)  # Shareable templates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("UserLiteratureReview")

class UserUpload(Base):
    """User's uploaded files (PDFs, documents)"""
    __tablename__ = "user_uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id"), nullable=False)
    filename = Column(String(255), nullable=False)  # Generated filename
    original_filename = Column(String(255), nullable=False)  # User's original filename
    file_path = Column(String(500), nullable=False)  # Path on disk
    file_type = Column(String(50), nullable=False)  # pdf, doc, txt, etc.
    file_size = Column(Integer, nullable=False)  # Size in bytes
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)  # When text extraction completed

    # Relationships
    user = relationship("LocalUser", back_populates="uploads")

class UserSearchHistory(Base):
    """User's search history for analytics"""
    __tablename__ = "user_search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id"), nullable=False)
    query = Column(String(500), nullable=False)
    category = Column(String(50), nullable=True)
    results_count = Column(Integer, default=0)
    searched_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("LocalUser", back_populates="search_history")

# Import Paper model for relationships
from app.models.paper import Paper
