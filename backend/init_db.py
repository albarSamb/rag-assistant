"""Script to initialize the database (create tables).

This is a development helper. In production, use Alembic migrations.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_db, engine
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message


async def main():
    """Initialize database tables."""
    print("[*] Initializing database...")
    
    try:
        await init_db()
        print("[OK] Database tables created successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - documents")
        print("  - conversations")
        print("  - messages")
    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        return 1
    finally:
        await engine.dispose()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
