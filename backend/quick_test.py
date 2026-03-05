"""Quick test script to process your own document."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag.pipeline import create_rag_pipeline
from app.rag.parser import detect_mime_type


def test_your_document(file_path: str):
    """Test RAG pipeline with your own document.
    
    Usage:
        python quick_test.py path/to/your/document.pdf
    """
    # Initialize pipeline
    print(f"\n[*] Initializing pipeline...")
    pipeline = create_rag_pipeline()
    
    # Detect file type
    mime_type = detect_mime_type(file_path)
    if not mime_type:
        print(f"[ERROR] Unsupported file type")
        return
    
    print(f"[*] Detected type: {mime_type}")
    
    # Process document
    print(f"[*] Processing: {file_path}")
    result = pipeline.process_document(
        file_path=file_path,
        mime_type=mime_type,
        document_id="test_doc",
        user_id="test_user"
    )
    
    if not result["success"]:
        print(f"[ERROR] {result.get('error')}")
        return
    
    print(f"[OK] Processed successfully!")
    print(f"  - Chunks: {result['chunk_count']}")
    print(f"  - Embedding dim: {result['embedding_dimension']}")
    
    # Test a query
    print(f"\n[*] Testing query...")
    question = input("Enter your question: ")
    
    query_result = pipeline.query(
        user_id="test_user",
        question=question,
        top_k=3
    )
    
    print(f"\n[+] Found {query_result['result_count']} results:\n")
    for i, res in enumerate(query_result["results"], 1):
        print(f"{i}. [Score: {res['similarity']:.3f}]")
        print(f"   {res['text'][:200]}...\n")
    
    # Cleanup
    print(f"\n[*] Cleaning up...")
    pipeline.delete_document("test_user", "test_doc")
    print(f"[OK] Done!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py <path_to_document>")
        print("\nSupported formats: PDF, Markdown (.md), TXT, DOCX")
        print("Example: python quick_test.py my_doc.pdf")
    else:
        file_path = sys.argv[1]
        if not Path(file_path).exists():
            print(f"[ERROR] File not found: {file_path}")
        else:
            test_your_document(file_path)
