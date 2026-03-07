"""LLM service for generating responses. Supports Groq (free) and Anthropic."""
from typing import AsyncGenerator, List, Dict, Any
import logging
import json
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMService:
    """Service for interacting with LLM providers (Groq or Anthropic)."""

    def __init__(self):
        """Initialize the LLM service based on configured provider."""
        self.provider = settings.LLM_PROVIDER.lower()
        self.max_tokens = 4096

        if self.provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                logger.warning("ANTHROPIC_API_KEY not set. Falling back to Groq.")
                self.provider = "groq"
            else:
                from anthropic import AsyncAnthropic
                self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                self.model = "claude-3-5-sonnet-20241022"

        if self.provider == "groq":
            if not settings.GROQ_API_KEY:
                logger.warning("GROQ_API_KEY not set. LLM will return an error message.")
            self.groq_api_key = settings.GROQ_API_KEY
            self.model = settings.GROQ_MODEL
            logger.info(f"Using Groq with model '{self.model}'")

    def build_rag_prompt(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Build prompt with RAG context."""
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

        history_text = ""
        if conversation_history:
            history_parts = []
            for msg in conversation_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_parts.append(f"{role.upper()}: {content}")
            history_text = "\n".join(history_parts)

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

    def _build_messages(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> list:
        """Build messages array for chat APIs."""
        prompt = self.build_rag_prompt(question, context_chunks, conversation_history)
        return [{"role": "user", "content": prompt}]

    async def generate_response(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using configured LLM provider."""
        if self.provider == "groq":
            async for chunk in self._generate_groq(question, context_chunks, conversation_history):
                yield chunk
        elif self.provider == "anthropic":
            async for chunk in self._generate_anthropic(question, context_chunks, conversation_history):
                yield chunk

    async def _generate_groq(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using Groq API."""
        if not self.groq_api_key:
            yield (
                "Error: GROQ_API_KEY not configured.\n"
                "1. Create a free account at https://console.groq.com\n"
                "2. Generate an API key\n"
                "3. Add GROQ_API_KEY=your_key to backend/.env"
            )
            return

        messages = self._build_messages(question, context_chunks, conversation_history)

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream(
                    "POST",
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": self.max_tokens,
                        "temperature": 0.7,
                        "stream": True,
                    },
                ) as response:
                    if response.status_code == 401:
                        yield "Error: Invalid GROQ_API_KEY. Check your key at https://console.groq.com"
                        return

                    if response.status_code != 200:
                        body = await response.aread()
                        yield f"Error: Groq API returned status {response.status_code}: {body.decode()}"
                        return

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

            logger.info("Groq response generated successfully")

        except httpx.ReadTimeout:
            yield "\n\nError: Response timed out."
        except Exception as e:
            logger.error(f"Error generating Groq response: {e}", exc_info=True)
            yield f"\n\nError generating response: {str(e)}"

    async def _generate_anthropic(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using Anthropic Claude API."""
        try:
            messages = self._build_messages(question, context_chunks, conversation_history)

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages,
                temperature=0.7
            ) as stream:
                async for text in stream.text_stream:
                    yield text

            logger.info("Anthropic response generated successfully")

        except Exception as e:
            logger.error(f"Error generating Anthropic response: {e}", exc_info=True)
            yield f"\n\nError generating response: {str(e)}"

    async def generate_response_non_streaming(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate non-streaming response (for testing)."""
        chunks = []
        async for chunk in self.generate_response(question, context_chunks, conversation_history):
            chunks.append(chunk)
        return "".join(chunks)


# Global singleton
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
