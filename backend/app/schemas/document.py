"""Document schemas for API requests and responses."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid


class DocumentBase(BaseModel):
    """Base document schema."""
    filename: str
    original_name: str
    mime_type: str


class DocumentCreate(DocumentBase):
    """Schema for creating a document (internal use)."""
    user_id: uuid.UUID
    file_size: int | None = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: uuid.UUID
    user_id: uuid.UUID
    file_size: int | None
    chunk_count: int
    processing_status: str
    error_message: str | None
    doc_metadata: dict
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Schema for list of documents."""
    documents: list[DocumentResponse]
    total: int


class DocumentProcessingStatus(BaseModel):
    """Schema for document processing status."""
    id: uuid.UUID
    status: str
    chunk_count: int
    error_message: str | None
