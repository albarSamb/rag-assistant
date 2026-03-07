"""Complete RAG pipeline integrating parsing, chunking, embedding, and retrieval."""
from typing import List, Dict, Any, Optional
import logging
import uuid
from pathlib import Path

from app.rag.parser import DocumentParser
from app.rag.chunker import RecursiveChunker
from app.rag.embedder import get_embedding_service
from app.rag.retriever import get_vector_retriever
from app.config import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Complete RAG pipeline for document processing and retrieval."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        top_k: int = None
    ):
        """Initialize the RAG pipeline.
        
        Args:
            chunk_size: Size of text chunks (uses config default if None)
            chunk_overlap: Overlap between chunks (uses config default if None)
            top_k: Number of results to retrieve (uses config default if None)
        """
        self.parser = DocumentParser()
        self.chunker = RecursiveChunker(
            chunk_size=chunk_size or settings.CHUNK_SIZE,
            chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP
        )
        self.embedding_service = get_embedding_service(settings.EMBEDDING_MODEL)
        self.retriever = get_vector_retriever(settings.CHROMA_PATH)
        self.top_k = top_k or settings.TOP_K_RESULTS
        
        logger.info("RAG Pipeline initialized")
    
    def process_document(
        self,
        file_path: str,
        mime_type: str,
        document_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a document through the complete pipeline.
        
        Steps:
        1. Parse document to extract text
        2. Chunk text into manageable pieces
        3. Generate embeddings for each chunk
        4. Store chunks and embeddings in vector database
        
        Args:
            file_path: Path to the document file
            mime_type: MIME type of the document
            document_id: Unique identifier for the document
            user_id: User who owns the document
            metadata: Additional metadata to attach
            
        Returns:
            Dictionary with processing results:
                - success: bool
                - chunk_count: int
                - document_metadata: dict
                - error: str (if failed)
        """
        try:
            logger.info(f"Processing document: {file_path} (user: {user_id})")
            
            # Step 1: Parse document
            parsed = self.parser.parse(file_path, mime_type)
            text = parsed["text"]
            doc_metadata = parsed["metadata"]
            
            if not text or len(text.strip()) < 10:
                raise ValueError("Document contains no extractable text")
            
            logger.info(f"Extracted {len(text)} characters from {Path(file_path).name}")
            
            # Step 2: Chunk text
            base_metadata = {
                "document_id": document_id,
                "user_id": user_id,
                "filename": Path(file_path).name,
                **(metadata or {}),
                **doc_metadata
            }
            
            chunks = self.chunker.split(text, metadata=base_metadata)
            logger.info(f"Created {len(chunks)} chunks")
            
            if not chunks:
                raise ValueError("No chunks created from document")
            
            # Step 3: Generate embeddings
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_service.embed_texts(chunk_texts)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 4: Store in vector database
            chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
            chunk_metadatas = [chunk.metadata for chunk in chunks]

            # Add chunk index to metadata and sanitize values for ChromaDB
            # ChromaDB only accepts str, int, float, bool — no None or complex types
            for i, meta in enumerate(chunk_metadatas):
                meta["chunk_index"] = i
                meta["chunk_total"] = len(chunks)
                for key in list(meta.keys()):
                    if meta[key] is None:
                        del meta[key]
                    elif not isinstance(meta[key], (str, int, float, bool)):
                        meta[key] = str(meta[key])
            
            self.retriever.add_chunks(
                user_id=user_id,
                chunk_ids=chunk_ids,
                texts=chunk_texts,
                embeddings=embeddings,
                metadatas=chunk_metadatas
            )
            
            logger.info(f"Successfully processed document {document_id}")
            
            return {
                "success": True,
                "chunk_count": len(chunks),
                "document_metadata": doc_metadata,
                "embedding_dimension": len(embeddings[0]) if embeddings else 0
            }
        
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "chunk_count": 0
            }
    
    def query(
        self,
        user_id: str,
        question: str,
        document_filter: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """Query the RAG system with a question.
        
        Args:
            user_id: User identifier
            question: Natural language question
            document_filter: Optional document ID to filter results
            top_k: Number of results to return (uses default if None)
            
        Returns:
            Dictionary with query results:
                - question: str
                - results: List[Dict] with chunk info
                - context: str (concatenated chunks for LLM)
        """
        try:
            logger.info(f"Querying for user {user_id}: '{question[:50]}...'")
            
            # Generate query embedding
            query_embedding = self.embedding_service.embed_query(question)
            
            # Search vector database
            filter_metadata = {"document_id": document_filter} if document_filter else None
            search_results = self.retriever.search(
                user_id=user_id,
                query_embedding=query_embedding,
                n_results=top_k or self.top_k,
                filter_metadata=filter_metadata
            )
            
            # Format results
            results = []
            for i in range(len(search_results["ids"])):
                results.append({
                    "chunk_id": search_results["ids"][i],
                    "text": search_results["documents"][i],
                    "metadata": search_results["metadatas"][i],
                    "distance": search_results["distances"][i],
                    "similarity": 1 - search_results["distances"][i]  # Convert distance to similarity
                })
            
            # Build context for LLM
            context = self._build_context(results)
            
            logger.info(f"Found {len(results)} relevant chunks")
            
            return {
                "question": question,
                "results": results,
                "context": context,
                "result_count": len(results)
            }
        
        except Exception as e:
            logger.error(f"Error querying RAG system: {e}", exc_info=True)
            return {
                "question": question,
                "results": [],
                "context": "",
                "error": str(e)
            }
    
    def _build_context(self, results: List[Dict[str, Any]]) -> str:
        """Build context string from search results for LLM.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            filename = metadata.get("filename", "Unknown")
            page = metadata.get("pages", "?")
            chunk_idx = metadata.get("chunk_index", "?")
            
            context_parts.append(
                f"[Source {i}: {filename}, Chunk {chunk_idx}]\n{result['text']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def delete_document(self, user_id: str, document_id: str) -> None:
        """Delete all chunks for a document.
        
        Args:
            user_id: User identifier
            document_id: Document identifier
        """
        self.retriever.delete_document_chunks(user_id, document_id)
        logger.info(f"Deleted chunks for document {document_id}")
    
    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user's documents.
        
        Args:
            user_id: User identifier
            
        Returns:
            Statistics dictionary
        """
        return self.retriever.get_collection_stats(user_id)


# Convenience function
def create_rag_pipeline(**kwargs) -> RAGPipeline:
    """Create a RAG pipeline instance.
    
    Args:
        **kwargs: Arguments to pass to RAGPipeline constructor
        
    Returns:
        RAGPipeline instance
    """
    return RAGPipeline(**kwargs)
