"""Vector retrieval service using ChromaDB."""
from typing import List, Dict, Optional, Any
import logging
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Service for storing and retrieving document chunks using ChromaDB."""
    
    def __init__(self, persist_directory: str = "./chroma_data"):
        """Initialize the vector retriever.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        logger.info(f"Initializing ChromaDB at: {persist_directory}")
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        logger.info("ChromaDB client initialized")
    
    def get_or_create_collection(
        self,
        user_id: str,
        embedding_function: Optional[Any] = None
    ) -> chromadb.Collection:
        """Get or create a collection for a user.
        
        Each user has their own collection to keep documents isolated.
        
        Args:
            user_id: User identifier
            embedding_function: Optional embedding function (we handle embeddings externally)
            
        Returns:
            ChromaDB collection
        """
        collection_name = f"user_{user_id}"
        
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine distance
            )
            logger.debug(f"Collection '{collection_name}' ready")
            return collection
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise
    
    def add_chunks(
        self,
        user_id: str,
        chunk_ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add document chunks to the vector store.
        
        Args:
            user_id: User identifier
            chunk_ids: List of unique chunk IDs
            texts: List of chunk texts
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts for each chunk
        """
        if not chunk_ids or len(chunk_ids) != len(texts) != len(embeddings) != len(metadatas):
            raise ValueError("All input lists must have the same non-zero length")
        
        collection = self.get_or_create_collection(user_id)
        
        try:
            collection.add(
                ids=chunk_ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Added {len(chunk_ids)} chunks to collection for user {user_id}")
        except Exception as e:
            logger.error(f"Error adding chunks: {e}")
            raise
    
    def search(
        self,
        user_id: str,
        query_embedding: List[float],
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar chunks using vector similarity.
        
        Args:
            user_id: User identifier
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filter_metadata: Optional metadata filter (e.g., {"document_id": "abc123"})
            
        Returns:
            Dictionary containing:
                - ids: List of chunk IDs
                - documents: List of chunk texts
                - metadatas: List of metadata dicts
                - distances: List of cosine distances (lower = more similar)
        """
        collection = self.get_or_create_collection(user_id)
        
        try:
            # Build query parameters
            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"]
            }
            
            # Add metadata filter if provided
            if filter_metadata:
                query_kwargs["where"] = filter_metadata
            
            results = collection.query(**query_kwargs)
            
            # ChromaDB returns lists of lists, flatten for single query
            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else []
            }
        except Exception as e:
            logger.error(f"Error searching collection: {e}")
            raise
    
    def delete_chunks(
        self,
        user_id: str,
        chunk_ids: Optional[List[str]] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Delete chunks from the vector store.
        
        Args:
            user_id: User identifier
            chunk_ids: Optional list of specific chunk IDs to delete
            filter_metadata: Optional metadata filter for deletion
        """
        collection = self.get_or_create_collection(user_id)
        
        try:
            if chunk_ids:
                collection.delete(ids=chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for user {user_id}")
            elif filter_metadata:
                collection.delete(where=filter_metadata)
                logger.info(f"Deleted chunks matching filter for user {user_id}")
            else:
                raise ValueError("Must provide either chunk_ids or filter_metadata")
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            raise
    
    def delete_document_chunks(self, user_id: str, document_id: str) -> None:
        """Delete all chunks for a specific document.
        
        Args:
            user_id: User identifier
            document_id: Document identifier
        """
        self.delete_chunks(
            user_id=user_id,
            filter_metadata={"document_id": document_id}
        )
    
    def get_collection_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about a user's collection.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with collection statistics
        """
        collection = self.get_or_create_collection(user_id)
        
        try:
            count = collection.count()
            return {
                "name": collection.name,
                "chunk_count": count,
                "metadata": collection.metadata
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise
    
    def reset_collection(self, user_id: str) -> None:
        """Delete and recreate a user's collection.
        
        WARNING: This deletes all data for the user.
        
        Args:
            user_id: User identifier
        """
        collection_name = f"user_{user_id}"
        
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            
            # Recreate empty collection
            self.get_or_create_collection(user_id)
            logger.info(f"Recreated collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise


# Global singleton instance
_vector_retriever: Optional[VectorRetriever] = None


def get_vector_retriever(persist_directory: str = "./chroma_data") -> VectorRetriever:
    """Get or create the global vector retriever instance.
    
    Args:
        persist_directory: Directory for ChromaDB persistence
        
    Returns:
        VectorRetriever instance
    """
    global _vector_retriever
    
    if _vector_retriever is None:
        _vector_retriever = VectorRetriever(persist_directory=persist_directory)
    
    return _vector_retriever
