"""Document parsing utilities for extracting text from various formats."""
from pathlib import Path
from typing import Optional, Dict
import logging

# PDF parsing
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Markdown parsing
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

# DOCX parsing
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


logger = logging.getLogger(__name__)


class DocumentParser:
    """Extract text from various document formats."""
    
    SUPPORTED_FORMATS = {
        "application/pdf": "pdf",
        "text/plain": "txt",
        "text/markdown": "md",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
    }
    
    def parse(self, file_path: str, mime_type: str) -> Dict[str, any]:
        """Parse a document and extract text and metadata.
        
        Args:
            file_path: Path to the document
            mime_type: MIME type of the document
            
        Returns:
            Dictionary containing:
                - text: Extracted text content
                - metadata: Document metadata (pages, title, etc.)
                
        Raises:
            ValueError: If format is not supported
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine parsing method based on MIME type
        if mime_type == "application/pdf":
            return self._parse_pdf(file_path)
        elif mime_type in ["text/plain", "text/markdown"]:
            return self._parse_text(file_path, is_markdown=(mime_type == "text/markdown"))
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported format: {mime_type}")
    
    def _parse_pdf(self, file_path: str) -> Dict[str, any]:
        """Extract text from PDF using PyPDF2 with pdfplumber fallback.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text and metadata
        """
        if not PDF_AVAILABLE:
            raise ImportError("PDF parsing libraries not installed. Install PyPDF2 and pdfplumber.")
        
        text_parts = []
        metadata = {
            "format": "pdf",
            "pages": 0,
            "title": None,
            "author": None
        }
        
        # Try PyPDF2 first (faster)
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)

                if pdf_reader.metadata:
                    metadata["title"] = pdf_reader.metadata.get('/Title', None)
                    metadata["author"] = pdf_reader.metadata.get('/Author', None)

                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Could not extract text from page {page_num}: {e}")
        except Exception as e:
            logger.warning(f"PyPDF2 failed for {file_path}: {e}, trying pdfplumber...")

        # Fallback to pdfplumber if PyPDF2 failed or extracted little text
        if len("".join(text_parts).strip()) < 100:
            logger.info("Trying pdfplumber for text extraction...")
            text_parts = []
            try:
                with pdfplumber.open(file_path) as pdf:
                    metadata["pages"] = len(pdf.pages)
                    for page_num, page in enumerate(pdf.pages, 1):
                        try:
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                        except Exception as e:
                            logger.warning(f"pdfplumber: Could not extract page {page_num}: {e}")
            except Exception as e:
                logger.error(f"pdfplumber also failed for {file_path}: {e}")
                raise ValueError(f"Could not parse PDF: both PyPDF2 and pdfplumber failed")
        
        full_text = "\n\n".join(text_parts)
        
        return {
            "text": full_text,
            "metadata": metadata
        }
    
    def _parse_text(self, file_path: str, is_markdown: bool = False) -> Dict[str, any]:
        """Extract text from plain text or markdown files.
        
        Args:
            file_path: Path to text file
            is_markdown: Whether the file is markdown format
            
        Returns:
            Extracted text and metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            metadata = {
                "format": "markdown" if is_markdown else "text",
                "char_count": len(text),
                "line_count": text.count('\n') + 1
            }
            
            # For markdown, we could optionally convert to plain text
            # but keeping markdown structure can be useful for chunking
            if is_markdown and MARKDOWN_AVAILABLE:
                # Keep raw markdown for now - can add HTML conversion if needed
                metadata["has_markdown"] = True
            
            return {
                "text": text,
                "metadata": metadata
            }
        
        except UnicodeDecodeError:
            # Try with different encoding
            logger.warning(f"UTF-8 decoding failed for {file_path}, trying latin-1")
            with open(file_path, 'r', encoding='latin-1') as file:
                text = file.read()
            
            return {
                "text": text,
                "metadata": {
                    "format": "text",
                    "encoding": "latin-1",
                    "char_count": len(text)
                }
            }
    
    def _parse_docx(self, file_path: str) -> Dict[str, any]:
        """Extract text from DOCX files.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text and metadata
        """
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not installed. Install it to parse DOCX files.")
        
        try:
            doc = docx.Document(file_path)
            
            # Extract paragraphs
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            text = "\n\n".join(paragraphs)
            
            metadata = {
                "format": "docx",
                "paragraph_count": len(paragraphs),
                "char_count": len(text)
            }
            
            # Extract core properties if available
            if hasattr(doc, 'core_properties'):
                props = doc.core_properties
                metadata["title"] = props.title
                metadata["author"] = props.author
                metadata["subject"] = props.subject
            
            return {
                "text": text,
                "metadata": metadata
            }
        
        except Exception as e:
            logger.error(f"Error parsing DOCX {file_path}: {e}")
            raise


def detect_mime_type(file_path: str) -> Optional[str]:
    """Detect MIME type from file extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        MIME type string or None
    """
    extension_to_mime = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".markdown": "text/markdown",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
    
    path = Path(file_path)
    ext = path.suffix.lower()
    
    return extension_to_mime.get(ext)
