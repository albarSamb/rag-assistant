"""Tests for text chunking module."""
import pytest
from app.rag.chunker import RecursiveChunker, TokenChunker, Chunk


class TestRecursiveChunker:
    """Test suite for RecursiveChunker."""
    
    def test_basic_chunking(self):
        """Test basic text chunking."""
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a test paragraph.\n\nThis is another paragraph.\n\nAnd a third one."
        
        chunks = chunker.split(text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.text for chunk in chunks)
    
    def test_chunk_size_respected(self):
        """Test that chunks don't exceed target size by much."""
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20)
        text = "Lorem ipsum dolor sit amet. " * 50  # Long text
        
        chunks = chunker.split(text)
        
        # Most chunks should be close to target size
        for chunk in chunks[:-1]:  # Exclude last chunk (may be smaller)
            assert len(chunk.text) <= 150  # Allow some flexibility
    
    def test_empty_text(self):
        """Test handling of empty text."""
        chunker = RecursiveChunker()
        chunks = chunker.split("")
        
        assert chunks == []
    
    def test_whitespace_only(self):
        """Test handling of whitespace-only text."""
        chunker = RecursiveChunker()
        chunks = chunker.split("   \n\n   ")
        
        assert chunks == []
    
    def test_overlap_functionality(self):
        """Test that overlap is created between chunks."""
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=15)
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here."
        
        chunks = chunker.split(text)
        
        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            for i in range(len(chunks) - 1):
                chunk1_end = chunks[i].text[-15:]
                chunk2_start = chunks[i + 1].text[:15]
                # There should be some common words
                assert any(word in chunk2_start for word in chunk1_end.split() if word)
    
    def test_chunk_metadata(self):
        """Test that metadata is preserved."""
        chunker = RecursiveChunker()
        metadata = {"source": "test.pdf", "page": 1}
        text = "This is a test."
        
        chunks = chunker.split(text, metadata=metadata)
        
        assert all(chunk.metadata == metadata for chunk in chunks)
    
    def test_chunk_indices(self):
        """Test that chunk indices are sequential."""
        chunker = RecursiveChunker(chunk_size=30, chunk_overlap=5)
        text = "Sentence one. Sentence two. Sentence three. Sentence four."
        
        chunks = chunker.split(text)
        
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
    
    def test_paragraph_splitting(self):
        """Test that paragraphs are respected when possible."""
        chunker = RecursiveChunker(chunk_size=200, chunk_overlap=20)
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        
        chunks = chunker.split(text)
        
        # With large chunk size, paragraphs should be kept together
        assert len(chunks) > 0
    
    def test_long_single_line(self):
        """Test handling of a single very long line."""
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=10)
        text = "word " * 200  # Very long single line
        
        chunks = chunker.split(text)
        
        assert len(chunks) > 1
        assert all(chunk.text.strip() for chunk in chunks)
    
    def test_custom_separators(self):
        """Test chunking with custom separators."""
        chunker = RecursiveChunker(
            chunk_size=50,
            chunk_overlap=5,
            separators=["|", ",", " "]
        )
        text = "Item1|Item2|Item3|Item4|Item5"
        
        chunks = chunker.split(text)
        
        assert len(chunks) > 0


class TestTokenChunker:
    """Test suite for TokenChunker."""
    
    def test_token_estimation(self):
        """Test token count estimation."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=10)
        text = "This is a test with multiple words and tokens."
        
        token_count = chunker._estimate_tokens(text)
        
        # Rough check: should be approximately len(text) / 4
        assert token_count > 0
        assert token_count < len(text)
    
    def test_token_chunking(self):
        """Test chunking by token count."""
        chunker = TokenChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a test paragraph. " * 20
        
        chunks = chunker.split(text)
        
        assert len(chunks) > 0
        # Each chunk should be roughly within token limit
        for chunk in chunks:
            tokens = chunker._estimate_tokens(chunk.text)
            assert tokens <= 80  # Allow some flexibility


class TestChunkDataclass:
    """Test Chunk dataclass."""
    
    def test_chunk_creation(self):
        """Test creating a Chunk object."""
        chunk = Chunk(
            text="Test text",
            chunk_index=0,
            start_char=0,
            end_char=9,
            metadata={"source": "test.txt"}
        )
        
        assert chunk.text == "Test text"
        assert chunk.chunk_index == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 9
        assert chunk.metadata == {"source": "test.txt"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
