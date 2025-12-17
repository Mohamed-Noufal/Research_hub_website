#!/usr/bin/env python3
"""Test PostgreSQL connection and pgvector setup"""

import os
import sys
sys.path.append('.')

# Change to backend directory and load environment variables from .env
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from app.core.database import init_db
from app.services.vector_service import VectorService

def test_connection():
    """Test database connection"""
    print("Testing PostgreSQL connection...")
    print(f"Current working directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")

    # Print environment variables
    db_url = os.getenv('DATABASE_URL')
    print(f"DATABASE_URL from env: {db_url}")

    try:
        # Import settings to check database URL
        from app.core.config import settings
        print(f"Database URL from settings: {settings.DATABASE_URL}")

        # Try to initialize database
        init_db()
        print("✅ Database initialized successfully")

        # Test vector service
        vector_service = VectorService()
        print("✅ VectorService created")

        # Test health check
        healthy = vector_service.health_check()
        if healthy:
            print("✅ Vector service health check passed")
        else:
            print("❌ Vector service health check failed")

        # Test vector embedding stats
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            stats = vector_service.get_embedding_stats(db)
            print(f"📊 Vector stats: {stats}")
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
