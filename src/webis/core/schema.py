"""
Core data models for Webis platform.

All data flowing through the system should conform to these schemas,
ensuring type safety and consistent interfaces across plugins.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict


class DocumentType(str, Enum):
    """Supported document types in Webis."""
    HTML = "html"
    PDF = "pdf"
    TEXT = "text"
    MARKDOWN = "markdown"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    JSON = "json"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    """Processing status of a document."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DocumentMetadata(BaseModel):
    """Metadata associated with a document."""
    
    model_config = ConfigDict(extra="allow")
    
    url: Optional[str] = Field(default=None, description="Source URL of the document")
    title: Optional[str] = Field(default=None, description="Document title")
    author: Optional[str] = Field(default=None, description="Document author")
    published_at: Optional[datetime] = Field(default=None, description="Publication date")
    fetched_at: datetime = Field(default_factory=datetime.now, description="Fetch timestamp")
    source_plugin: Optional[str] = Field(default=None, description="Plugin that fetched this document")
    language: Optional[str] = Field(default=None, description="Document language (ISO 639-1)")
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata fields")


class DocumentChunk(BaseModel):
    """A chunk of text from a document."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebisDocument(BaseModel):
    """
    The fundamental data unit in Webis system.
    
    Represents a single piece of content flowing through the pipeline,
    from raw acquisition to structured extraction.
    
    Example:
        >>> doc = WebisDocument(
        ...     content="<html>...</html>",
        ...     doc_type=DocumentType.HTML,
        ...     meta=DocumentMetadata(url="https://example.com")
        ... )
    """
    
    model_config = ConfigDict(frozen=False)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique document ID")
    content: str = Field(..., description="Raw content of the document")
    clean_content: Optional[str] = Field(default=None, description="Cleaned/extracted text content")
    doc_type: DocumentType = Field(default=DocumentType.UNKNOWN, description="Type of the document")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING, description="Processing status")
    meta: DocumentMetadata = Field(default_factory=DocumentMetadata, description="Document metadata")
    
    # Processing artifacts
    chunks: List["DocumentChunk"] = Field(default_factory=list, description="Text chunks for embedding")
    embeddings: Optional[List[List[float]]] = Field(default=None, description="Vector embeddings")
    
    # Lineage tracking
    parent_id: Optional[str] = Field(default=None, description="Parent document ID (for derived docs)")
    processing_history: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Record of processing steps applied"
    )
    
    def add_processing_step(self, plugin_name: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Record a processing step in the document's history."""
        self.processing_history.append({
            "plugin": plugin_name,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(mode="json")


class DocumentChunk(BaseModel):
    """A chunk of text extracted from a document, ready for embedding."""
    
    text: str = Field(..., description="Chunk text content")
    index: int = Field(..., description="Chunk index within the document")
    start_char: Optional[int] = Field(default=None, description="Start character position")
    end_char: Optional[int] = Field(default=None, description="End character position")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk-level metadata")


class Lineage(BaseModel):
    """Tracks the provenance of structured data."""
    
    source_doc_ids: List[str] = Field(..., description="Source document IDs")
    prompt_version: Optional[str] = Field(default=None, description="Prompt template version used")
    model_name: Optional[str] = Field(default=None, description="LLM model used for extraction")
    extracted_at: datetime = Field(default_factory=datetime.now, description="Extraction timestamp")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Extraction confidence score")


class StructuredResult(BaseModel):
    """
    The output of structured extraction from documents.
    
    Contains the extracted data along with provenance information
    for traceability and quality assessment.
    
    Example:
        >>> result = StructuredResult(
        ...     schema_id="news_article",
        ...     data={"title": "...", "summary": "..."},
        ...     lineage=Lineage(source_doc_ids=["doc-123"])
        ... )
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Result ID")
    schema_id: str = Field(..., description="ID of the extraction schema/template used")
    data: Union[Dict[str, Any], List[Any]] = Field(..., description="Extracted structured data")
    raw_output: Optional[str] = Field(default=None, description="Raw LLM output before parsing")
    lineage: Lineage = Field(..., description="Provenance information")
    
    # Quality indicators
    is_valid: bool = Field(default=True, description="Whether the output passed schema validation")
    validation_errors: List[str] = Field(default_factory=list, description="Schema validation errors")
    needs_review: bool = Field(default=False, description="Flag for human review")


class PipelineContext(BaseModel):
    """
    Context object passed through the entire pipeline execution.
    
    Contains configuration, logging, and state shared across all plugins.
    """
    
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique pipeline run ID")
    task: str = Field(..., description="User-specified task/goal")
    config: Dict[str, Any] = Field(default_factory=dict, description="Pipeline configuration")
    
    # Execution state
    started_at: datetime = Field(default_factory=datetime.now, description="Pipeline start time")
    current_stage: Optional[str] = Field(default=None, description="Current processing stage")
    
    # Execution flags
    is_dry_run: bool = Field(default=False, description="If True, skip side-effects and LLM calls")
    is_debug: bool = Field(default=False, description="If True, enable verbose logging and intermediate outputs")
    tenant_id: Optional[str] = Field(default=None, description="Tenant ID for multi-tenant isolation")

    # Resource tracking
    total_tokens_used: int = Field(default=0, description="Total LLM tokens consumed")
    total_cost_usd: float = Field(default=0.0, description="Estimated cost in USD")
    
    # Output paths
    output_dir: Optional[str] = Field(default=None, description="Output directory path")
    
    # Shared state
    state: Dict[str, Any] = Field(default_factory=dict, description="Shared state across plugins")

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value
        
    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)
    
    def log_tokens(self, tokens: int, cost: float = 0.0) -> None:
        """Record token usage and cost."""
        self.total_tokens_used += tokens
        self.total_cost_usd += cost


# Re-export for convenience
__all__ = [
    "DocumentType",
    "DocumentStatus",
    "DocumentMetadata",
    "WebisDocument",
    "DocumentChunk",
    "Lineage",
    "StructuredResult",
    "PipelineContext",
]
