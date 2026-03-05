"""RAG-specific schemas."""
from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    """Schema for RAG query request."""
    question: str
    document_filter: str | None = None
    top_k: int = 5


class RAGChunk(BaseModel):
    """Schema for a RAG chunk/source."""
    chunk_id: str
    text: str
    metadata: dict
    distance: float
    similarity: float


class RAGQueryResponse(BaseModel):
    """Schema for RAG query response."""
    question: str
    results: list[RAGChunk]
    context: str
    result_count: int
