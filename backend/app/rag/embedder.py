"""Embedding service for text vectorization using sentence-transformers."""
from typing import List, Optional
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers.
    
    Uses the 'all-MiniLM-L6-v2' model by default (384 dimensions, fast, good quality).
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        logger.info(f"Embedding service initialized with model: {model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the model on first use.
        
        Returns:
            Loaded SentenceTransformer model
        """
        if self._model is None:
            logger.info(f"Loading model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded. Embedding dimension: {self.get_dimension()}")
        return self._model
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Batch size for encoding
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        if not texts:
            return []
        
        logger.debug(f"Embedding {len(texts)} texts...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Convert numpy arrays to lists for JSON serialization
        return embeddings.tolist()
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query text.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        logger.debug(f"Embedding query: '{query[:50]}...'")
        embedding = self.model.encode(
            query,
            convert_to_numpy=True
        )
        
        return embedding.tolist()
    
    def get_dimension(self) -> int:
        """Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension (e.g., 384 for all-MiniLM-L6-v2)
        """
        return self.model.get_sentence_embedding_dimension()
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (between -1 and 1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# Global singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingService:
    """Get or create the global embedding service instance.
    
    Args:
        model_name: Name of the model to use
        
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name=model_name)
    
    return _embedding_service
