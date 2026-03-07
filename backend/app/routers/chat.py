"""Chat endpoints with SSE streaming."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Annotated, AsyncGenerator
import uuid
import json
from datetime import datetime

from app.database import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.schemas.chat import (
    ConversationCreate,
    ConversationSummary,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    ChatRequest
)
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundException
from app.rag.pipeline import RAGPipeline
from app.services.llm import get_llm_service
from app.config import settings

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]


async def format_sse_message(data: dict) -> str:
    """Format data as Server-Sent Event.
    
    Args:
        data: Dictionary to send
        
    Returns:
        Formatted SSE message
    """
    return f"data: {json.dumps(data)}\n\n"


@router.post("/", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation.
    
    Args:
        conversation_data: Conversation creation data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created conversation
    """
    conversation = Conversation(
        user_id=current_user.id,
        title=conversation_data.title or "New Conversation"
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return conversation


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """List all conversations for the current user.
    
    Args:
        current_user: Authenticated user
        db: Database session
        skip: Pagination offset
        limit: Max results
        
    Returns:
        List of conversations
    """
    # Get total count
    count_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == current_user.id)
    )
    total = count_result.scalar_one()
    
    # Get conversations
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    conversations = result.scalars().all()
    
    return ConversationListResponse(conversations=conversations, total=total)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific conversation with all messages.
    
    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Conversation with messages
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise NotFoundException("Conversation not found")

    # Load messages separately to avoid sync lazy-load on async session
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    msgs = messages_result.scalars().all()

    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=msgs,
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages in a conversation.
    
    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of messages
    """
    # Verify conversation belongs to user
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = conv_result.scalar_one_or_none()
    
    if not conversation:
        raise NotFoundException("Conversation not found")
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    
    return messages


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    message_data: MessageCreate,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get streaming response.
    
    This endpoint returns Server-Sent Events (SSE) for real-time streaming.
    
    Args:
        conversation_id: Conversation ID
        message_data: Message content
        current_user: Authenticated user
        db: Database session
        
    Returns:
        StreamingResponse with SSE
    """
    # Verify conversation exists and belongs to user
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise NotFoundException("Conversation not found")

    # Capture values needed in the stream (db session will be closed after return)
    user_id = str(current_user.id)
    question = message_data.content
    doc_filter = str(message_data.document_filter) if message_data.document_filter else None

    # Stream response — uses its own db session since FastAPI closes the
    # dependency session before the StreamingResponse generator runs
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE stream with RAG + LLM response."""
        async with AsyncSessionLocal() as stream_db:
            try:
                # Save user message
                user_message = Message(
                    conversation_id=conversation_id,
                    role="user",
                    content=question,
                    sources=[]
                )
                stream_db.add(user_message)
                await stream_db.commit()

                # Step 1: Send event indicating start
                yield await format_sse_message({"event": "start", "message": "Processing query..."})

                # Step 2: RAG retrieval
                yield await format_sse_message({"event": "retrieval", "message": "Searching documents..."})

                pipeline = RAGPipeline()

                # Query RAG pipeline
                rag_result = pipeline.query(
                    user_id=user_id,
                    question=question,
                    document_filter=doc_filter,
                    top_k=5
                )

                context_chunks = rag_result.get("results", [])

                # Normalize chunk format: pipeline returns "text", LLM expects "content"
                for chunk in context_chunks:
                    if "text" in chunk and "content" not in chunk:
                        chunk["content"] = chunk["text"]

                # Send sources info
                sources_info = [
                    {
                        "content": chunk.get("content", chunk.get("text", ""))[:200] + "...",
                        "metadata": chunk.get("metadata", {}),
                        "score": chunk.get("similarity", 0.0)
                    }
                    for chunk in context_chunks
                ]

                yield await format_sse_message({
                    "event": "sources",
                    "count": len(context_chunks),
                    "sources": sources_info
                })

                # Step 3: Get conversation history
                history_result = await stream_db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at.desc())
                    .limit(10)
                )
                history_messages = history_result.scalars().all()
                conversation_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in reversed(history_messages)
                ]

                # Step 4: Generate response with LLM
                yield await format_sse_message({"event": "generating", "message": "Generating response..."})

                llm_service = get_llm_service()
                full_response = ""

                async for chunk in llm_service.generate_response(
                    question=question,
                    context_chunks=context_chunks,
                    conversation_history=conversation_history
                ):
                    full_response += chunk
                    yield await format_sse_message({
                        "event": "token",
                        "content": chunk
                    })

                # Step 5: Save assistant message
                assistant_message = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                    sources=sources_info
                )
                stream_db.add(assistant_message)

                # Update conversation timestamp
                conv_result2 = await stream_db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conv = conv_result2.scalar_one_or_none()
                if conv:
                    conv.updated_at = datetime.utcnow()

                await stream_db.commit()

                # Send completion event
                yield await format_sse_message({
                    "event": "done",
                    "message_id": str(assistant_message.id)
                })

            except Exception as e:
                # Send error event
                yield await format_sse_message({
                    "event": "error",
                    "error": str(e)
                })
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation and all its messages.
    
    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user
        db: Database session
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise NotFoundException("Conversation not found")
    
    await db.delete(conversation)
    await db.commit()
    
    return None
