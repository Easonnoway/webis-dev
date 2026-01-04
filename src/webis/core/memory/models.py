"""
SQLModel definitions for Webis persistence layer.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel, Relationship

class DocumentModel(SQLModel, table=True):
    """
    Database model for WebisDocument.
    """
    __tablename__ = "documents"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    content: str = Field(sa_column_kwargs={"nullable": False})
    clean_content: Optional[str] = Field(default=None)
    doc_type: str = Field(index=True)
    
    # Metadata fields flattened or stored as JSON
    url: Optional[str] = Field(default=None, index=True)
    content_hash: Optional[str] = Field(default=None, index=True)
    title: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    published_at: Optional[datetime] = Field(default=None)
    source_plugin: Optional[str] = Field(default=None, index=True)
    
    # Complex metadata stored as JSON
    meta_custom: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    
    # Lineage
    parent_id: Optional[str] = Field(default=None, index=True)
    processing_history: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RunModel(SQLModel, table=True):
    """
    Track pipeline execution runs.
    """
    __tablename__ = "runs"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    pipeline_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    status: str = Field(default="pending")
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    total_tokens: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    
    error: Optional[str] = Field(default=None)
