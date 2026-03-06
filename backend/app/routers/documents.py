"""Documents CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Annotated
import uuid
import os
import shutil
from pathlib import Path

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentProcessingStatus
)
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundException
from app.config import settings

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/markdown",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

# Maximum file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


async def process_document_task(document_id: str, user_id: str, file_path: str, mime_type: str):
    """Background task to process document through RAG pipeline."""
    from app.database import AsyncSessionLocal
    from app.rag.pipeline import RAGPipeline
    
    # Create new DB session for background task
    async with AsyncSessionLocal() as db:
        try:
            # Update status to processing
            result = await db.execute(
                select(Document).where(Document.id == uuid.UUID(document_id))
            )
            document = result.scalar_one_or_none()
            if not document:
                return
            
            document.processing_status = "processing"
            await db.commit()
            
            # Run RAG pipeline
            pipeline = RAGPipeline()
            result = pipeline.process_document(
                file_path=file_path,
                mime_type=mime_type,
                document_id=document_id,
                user_id=user_id
            )
            
            # Update status to completed
            document.processing_status = "completed"
            document.chunk_count = result.get("chunk_count", 0)
            await db.commit()
            
        except Exception as e:
            # Update status to failed
            result = await db.execute(
                select(Document).where(Document.id == uuid.UUID(document_id))
            )
            document = result.scalar_one_or_none()
            if document:
                document.processing_status = "failed"
                document.error_message = str(e)
                await db.commit()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document file.
    
    The file will be saved and processed in the background through the RAG pipeline.
    Supported formats: PDF, Markdown, TXT, DOCX
    """
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Read file to check size
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024} MB"
        )
    
    # Create uploads directory if not exists
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = uploads_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create document record
    document = Document(
        user_id=current_user.id,
        filename=unique_filename,
        original_name=file.filename,
        mime_type=file.content_type,
        file_size=file_size,
        processing_status="pending",
        doc_metadata={}
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Add background task to process document
    background_tasks.add_task(
        process_document_task,
        str(document.id),
        str(current_user.id),
        str(file_path),
        file.content_type
    )
    
    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all documents for the current user.
    
    Supports pagination with skip and limit parameters.
    """
    # Get total count
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.user_id == current_user.id)
    )
    total = count_result.scalar_one()
    
    # Get documents
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()
    
    return DocumentListResponse(documents=documents, total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific document by ID.
    
    Only returns document if it belongs to the current user.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise NotFoundException("Document not found")
    
    return document


@router.get("/{document_id}/status", response_model=DocumentProcessingStatus)
async def get_document_status(
    document_id: uuid.UUID,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the processing status of a document.
    
    Useful for polling while document is being processed.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise NotFoundException("Document not found")
    
    return DocumentProcessingStatus(
        id=document.id,
        status=document.processing_status,
        chunk_count=document.chunk_count,
        error_message=document.error_message
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document.
    
    Removes the file from disk, database record, and vectors from ChromaDB.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise NotFoundException("Document not found")
    
    # Delete file from disk
    file_path = Path(settings.uploads_dir) / document.filename
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass  # Continue even if file deletion fails
    
    # Delete vectors from ChromaDB
    try:
        from app.rag.retriever import get_vector_retriever
        retriever = get_vector_retriever()
        retriever.delete_document_chunks(
            user_id=str(current_user.id),
            document_id=str(document_id)
        )
    except Exception:
        pass  # Continue even if vector deletion fails
    
    # Delete from database
    await db.delete(document)
    await db.commit()
    
    return None
