"""Text chunking utilities for RAG pipeline.

This module implements intelligent text splitting strategies for breaking down
large documents into manageable chunks while preserving semantic context.
"""
from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict


class RecursiveChunker:
    """Recursive text chunker with overlap.
    
    Splits text using a hierarchy of separators:
    1. Paragraphs (\\n\\n)
    2. Lines (\\n)
    3. Sentences (. )
    4. Words ( )
    
    This preserves semantic boundaries when possible.
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
        length_function: callable = len
    ):
        """Initialize chunker.
        
        Args:
            chunk_size: Target size for each chunk (in characters by default)
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators in priority order
            length_function: Function to measure text length (default: character count)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self.length_function = length_function
    
    def split(self, text: str, metadata: Optional[dict] = None) -> List[Chunk]:
        """Split text into chunks with overlap.
        
        Args:
            text: Text to split
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        chunks = []
        current_position = 0
        chunk_index = 0
        
        # Get splits from recursive splitting
        splits = self._split_text(text, self.separators)
        
        # Merge splits into chunks of appropriate size
        merged_chunks = self._merge_splits(splits, text)
        
        for chunk_text in merged_chunks:
            if chunk_text.strip():
                chunk = Chunk(
                    text=chunk_text.strip(),
                    chunk_index=chunk_index,
                    start_char=current_position,
                    end_char=current_position + len(chunk_text),
                    metadata=metadata.copy()
                )
                chunks.append(chunk)
                chunk_index += 1
                current_position += len(chunk_text)
        
        return chunks
    
    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using separators.
        
        Args:
            text: Text to split
            separators: List of separators to try
            
        Returns:
            List of text segments
        """
        final_chunks = []
        separator = separators[-1]
        new_separators = []
        
        # Try each separator in order
        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                break
            if re.search(re.escape(sep), text):
                separator = sep
                new_separators = separators[i + 1:]
                break
        
        # Split on the chosen separator
        splits = text.split(separator) if separator else list(text)
        
        # Process each split
        good_splits = []
        for split in splits:
            if self.length_function(split) < self.chunk_size:
                good_splits.append(split)
            else:
                # If still too large, split recursively with next separators
                if new_separators:
                    good_splits.extend(self._split_text(split, new_separators))
                else:
                    good_splits.append(split)
        
        # Re-add separators
        if separator and separator != "":
            for i in range(len(good_splits) - 1):
                good_splits[i] += separator
        
        return good_splits
    
    def _merge_splits(self, splits: List[str], original_text: str) -> List[str]:
        """Merge small splits into chunks of target size with overlap.
        
        Args:
            splits: List of text segments to merge
            original_text: Original text (for context)
            
        Returns:
            List of merged chunks
        """
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_length = self.length_function(split)
            
            # If adding this split exceeds chunk_size, finalize current chunk
            if current_length + split_length > self.chunk_size and current_chunk:
                chunks.append("".join(current_chunk))
                
                # Handle overlap: keep last part of current chunk
                overlap_text = self._get_overlap_text(current_chunk, current_length)
                current_chunk = [overlap_text] if overlap_text else []
                current_length = self.length_function(overlap_text) if overlap_text else 0
            
            # Add split to current chunk
            current_chunk.append(split)
            current_length += split_length
        
        # Add final chunk
        if current_chunk:
            chunks.append("".join(current_chunk))
        
        return chunks
    
    def _get_overlap_text(self, chunk_parts: List[str], total_length: int) -> str:
        """Get overlap text from end of chunk.
        
        Args:
            chunk_parts: Parts that make up the current chunk
            total_length: Total length of current chunk
            
        Returns:
            Text to use for overlap
        """
        if self.chunk_overlap == 0 or total_length <= self.chunk_overlap:
            return ""
        
        # Get text from the end equal to overlap size
        full_text = "".join(chunk_parts)
        return full_text[-self.chunk_overlap:]


class TokenChunker(RecursiveChunker):
    """Chunker that splits by token count instead of character count.
    
    Uses a simple whitespace-based token approximation (4 chars ≈ 1 token).
    For production, consider using tiktoken for accurate token counting.
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """Initialize token-based chunker.
        
        Args:
            chunk_size: Target size in tokens
            chunk_overlap: Overlap size in tokens
            separators: List of separators
        """
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=self._estimate_tokens
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation).
        
        Args:
            text: Text to measure
            
        Returns:
            Estimated token count
        """
        # Simple approximation: 1 token ≈ 4 characters
        return len(text) // 4
