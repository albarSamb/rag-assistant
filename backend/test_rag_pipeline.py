"""End-to-end test script for the RAG pipeline.

This script demonstrates the complete RAG workflow:
1. Create a test document
2. Process it through the pipeline
3. Query the system
4. Display results
"""
import sys
import os
from pathlib import Path
import tempfile
import logging

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.rag.pipeline import create_rag_pipeline
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_markdown():
    """Create a test markdown document."""
    content = """# FastAPI Documentation Test

## Introduction to FastAPI

FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.

### Key Features

1. **Fast**: Very high performance, on par with NodeJS and Go
2. **Fast to code**: Increase the speed to develop features by about 200% to 300%
3. **Fewer bugs**: Reduce about 40% of human (developer) induced errors
4. **Intuitive**: Great editor support with autocompletion everywhere
5. **Easy**: Designed to be easy to use and learn
6. **Short**: Minimize code duplication

## Creating Your First API

Here's a simple example of a FastAPI application:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

## Middleware and Authentication

FastAPI supports middleware for various purposes including authentication.

### Creating an Authentication Middleware

You can create a middleware that checks for authentication tokens:

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    response = await call_next(request)
    return response
```

### Using Dependencies for Auth

A better approach is using dependency injection:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "secret-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return credentials.credentials

@app.get("/protected")
async def protected_route(token: str = Depends(verify_token)):
    return {"message": "Access granted", "token": token}
```

## Database Integration

FastAPI works great with SQLAlchemy for database operations.

### Async Database Setup

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session():
    async with async_session() as session:
        yield session
```

## Best Practices

1. Use type hints for automatic validation
2. Leverage dependency injection for cleaner code
3. Use async/await for better performance
4. Implement proper error handling
5. Document your API with docstrings

---

Learn more at: https://fastapi.tiangolo.com
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.md',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(content)
        return f.name


def main():
    """Run the end-to-end test."""
    print("=" * 70)
    print("RAG PIPELINE END-TO-END TEST")
    print("=" * 70)
    
    # Create test document
    print("\nCreating test document...")
    test_file = create_test_markdown()
    test_filename = Path(test_file).name
    print(f"Created: {test_filename}")
    
    # Initialize pipeline
    print("\nInitializing RAG pipeline...")
    pipeline = create_rag_pipeline()
    print("Pipeline ready")
    
    # Test user
    user_id = "test_user_123"
    document_id = "test_doc_001"
    
    try:
        # Process document
        print(f"\n[*] Processing document...")
        result = pipeline.process_document(
            file_path=test_file,
            mime_type="text/markdown",
            document_id=document_id,
            user_id=user_id,
            metadata={"source": "test"}
        )
        
        if result["success"]:
            print(f"[OK] Document processed successfully!")
            print(f"  - Chunks created: {result['chunk_count']}")
            print(f"  - Embedding dimension: {result['embedding_dimension']}")
        else:
            print(f"✗ Processing failed: {result.get('error')}")
            return
        
        # Get stats
        print(f"\n[*] Collection stats:")
        stats = pipeline.get_stats(user_id)
        print(f"  - Total chunks: {stats['chunk_count']}")
        
        # Test queries
        test_questions = [
            "How do I create an authentication middleware with FastAPI?",
            "What are the key features of FastAPI?",
            "How do I setup an async database connection?"
        ]
        
        print("\n" + "=" * 70)
        print("TESTING QUERIES")
        print("=" * 70)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'-' * 70}")
            print(f"Question {i}: {question}")
            print(f"{'-' * 70}")
            
            query_result = pipeline.query(
                user_id=user_id,
                question=question,
                top_k=3
            )
            
            if query_result["results"]:
                print(f"\n[+] Found {query_result['result_count']} relevant chunks:\n")
                
                for j, res in enumerate(query_result["results"], 1):
                    similarity = res["similarity"]
                    chunk_preview = res["text"][:200] + "..." if len(res["text"]) > 200 else res["text"]
                    
                    print(f"  {j}. [Similarity: {similarity:.3f}]")
                    print(f"     Chunk {res['metadata']['chunk_index']}/{res['metadata']['chunk_total']}")
                    print(f"     {chunk_preview}\n")
                
                # Show context that would be sent to LLM
                print(f"\n[*] Context for LLM (preview):")
                context_preview = query_result["context"][:500]
                print(f"{context_preview}...\n")
            else:
                print("[!] No results found")
        
        # Clean up
        print("\n" + "=" * 70)
        print("CLEANUP")
        print("=" * 70)
        
        print(f"\nDeleting document chunks...")
        pipeline.delete_document(user_id, document_id)
        print("[OK] Chunks deleted")
        
        final_stats = pipeline.get_stats(user_id)
        print(f"[OK] Final chunk count: {final_stats['chunk_count']}")
        
    finally:
        # Remove test file
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"[OK] Removed test file: {test_filename}")
    
    print("\n" + "=" * 70)
    print("[SUCCESS] TEST COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
