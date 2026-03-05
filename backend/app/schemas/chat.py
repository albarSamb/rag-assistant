"""Chat/conversation schemas for API requests and responses."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid


class MessageBase(BaseModel):
    """Base message schema."""
    role: str
    content: str


class MessageCreate(BaseModel):
    """Schema for creating a message."""
    content: str
    document_filter: uuid.UUID | None = None  # Optional: filter by specific document


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: uuid.UUID
    conversation_id: uuid.UUID
    sources: list[dict]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: str | None = None


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    pass


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    """Schema for list of conversations."""
    conversations: list[ConversationResponse]
    total: int


class ChatRequest(BaseModel):
    """Schema for chat message request."""
    message: str
    conversation_id: uuid.UUID | None = None  # Optional: create new if not provided
    document_filter: uuid.UUID | None = None  # Optional: filter by specific document


class ChatResponse(BaseModel):
    """Schema for chat response (streaming)."""
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    content: str
    sources: list[dict]
