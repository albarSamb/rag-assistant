"""LLM service for generating responses with Claude API."""
from typing import AsyncGenerator, List, Dict, Any
import logging
from anthropic import AsyncAnthropic
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Claude API."""
    
    def __init__(self):
        """Initialize the LLM service."""
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set. LLM service will not work.")
            self.client = None
        else:
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 4096
    
    def build_rag_prompt(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Build prompt with RAG context.
        
        Args:
            question: User's question
            context_chunks: Retrieved chunks from vector DB
            conversation_history: Previous messages in conversation
            
        Returns:
            Formatted prompt
        """
        # Build context section from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            chunk_index = metadata.get("chunk_index", "?")
            
            context_parts.append(
                f"[Source {i}] (File: {filename}, Chunk: {chunk_index})\n{content}"
            )
        
        context_text = "\n\n".join(context_parts) if context_parts else "No relevant context found."
        
        # Build conversation history
        history_text = ""
        if conversation_history:
            history_parts = []
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_parts.append(f"{role.upper()}: {content}")
            history_text = "\n".join(history_parts)
        
        # Build final prompt
        prompt = f"""You are a helpful AI assistant that answers questions based on provided documentation.

IMPORTANT INSTRUCTIONS:
- Answer the question using ONLY the information from the provided context
- If the context doesn't contain enough information to answer, say so clearly
- Cite specific sources when possible (e.g., "According to Source 1...")
- Be concise but comprehensive
- If asked about something not in the context, acknowledge the limitation

CONTEXT FROM DOCUMENTATION:
{context_text}
"""
        
        if history_text:
            prompt += f"\n\nPREVIOUS CONVERSATION:\n{history_text}\n"
        
        prompt += f"\n\nUSER QUESTION:\n{question}\n\nASSISTANT RESPONSE:"
        
        return prompt
    
    async def generate_response(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using Claude API.
        
        Args:
            question: User's question
            context_chunks: Retrieved chunks from vector DB
            conversation_history: Previous messages
            
        Yields:
            Response chunks as they arrive
        """
        if not self.client:
            yield "Error: ANTHROPIC_API_KEY not configured. Please set your API key in .env file."
            return
        
        try:
            prompt = self.build_rag_prompt(question, context_chunks, conversation_history)
            
            logger.info(f"Generating response for question: {question[:50]}...")
            
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7
            ) as stream:
                async for text in stream.text_stream:
                    yield text
            
            logger.info("Response generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            yield f"\n\nError generating response: {str(e)}"
    
    async def generate_response_non_streaming(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate non-streaming response (for testing).
        
        Args:
            question: User's question
            context_chunks: Retrieved chunks
            conversation_history: Previous messages
            
        Returns:
            Complete response text
        """
        if not self.client:
            return "Error: ANTHROPIC_API_KEY not configured."
        
        try:
            prompt = self.build_rag_prompt(question, context_chunks, conversation_history)
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return f"Error: {str(e)}"


# Global singleton
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance.
    
    Returns:
        LLMService instance
    """
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService()
    
    return _llm_service
