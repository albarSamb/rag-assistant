"""Document model."""
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Document(Base):
    """Document metadata model."""
    
    __tablename__ = "documents"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # File Information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer)
    
    # Processing Status
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True
    )  # pending | processing | completed | failed
    error_message: Mapped[str | None] = mapped_column(Text)
    
    # Metadata (JSON field for flexible storage)
    doc_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="documents")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.processing_status})>"
