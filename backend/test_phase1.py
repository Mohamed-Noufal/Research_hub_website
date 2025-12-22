"""
Verification script for Phase 1 setup
Tests database tables, dependencies, and configuration
"""
import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import sys

load_dotenv()

async def test_database():
    """Test database connection and tables"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    
    try:
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Test pgvector
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            pgvector = result.fetchone()
            if pgvector:
                print(f"✅ pgvector extension installed (version {pgvector[2]})")
            else:
                print("❌ pgvector not installed")
                return False
            
            # Test tables
            tables = [
                'paper_chunks',
                'agent_conversations',
                'agent_messages',
                'agent_tool_calls',
                'llm_usage_logs',
                'rag_usage_logs'
            ]
            
            print("\n📋 Checking agent system tables:")
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"   ✅ {table} exists (rows: {count})")
                except Exception as e:
                    print(f"   ❌ {table} missing or error: {e}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_dependencies():
    """Test if required packages are installed"""
    print("\n📦 Checking dependencies:")
    
    packages = [
        ('llama_index.core', 'LlamaIndex'),
        ('groq', 'Groq'),
        ('pgvector', 'pgvector'),
        ('sentence_transformers', 'sentence-transformers'),
        ('tiktoken', 'tiktoken'),
        ('tenacity', 'tenacity'),
        ('websockets', 'websockets')
    ]
    
    all_installed = True
    for package, name in packages:
        try:
            __import__(package)
            print(f"   ✅ {name} installed")
        except ImportError:
            print(f"   ❌ {name} not installed")
            all_installed = False
    
    return all_installed

def test_configuration():
    """Test configuration settings"""
    print("\n⚙️  Checking configuration:")
    
    from app.core.config import settings
    
    required_settings = [
        ('DATABASE_URL', settings.DATABASE_URL),
        ('GROQ_API_KEY', settings.GROQ_API_KEY),
        ('AGENT_MAX_ITERATIONS', settings.AGENT_MAX_ITERATIONS),
        ('EMBEDDING_MODEL', settings.EMBEDDING_MODEL),
    ]
    
    all_configured = True
    for name, value in required_settings:
        if value:
            # Mask sensitive values
            display_value = value if name not in ['GROQ_API_KEY', 'DATABASE_URL'] else '***'
            print(f"   ✅ {name}: {display_value}")
        else:
            print(f"   ⚠️  {name}: not set")
            if name == 'GROQ_API_KEY':
                print(f"      (Optional for Phase 1, required for Phase 2)")
            else:
                all_configured = False
    
    return all_configured

async def main():
    print("=" * 60)
    print("🧪 Phase 1 Verification Test")
    print("=" * 60)
    
    db_ok = await test_database()
    deps_ok = test_dependencies()
    config_ok = test_configuration()
    
    print("\n" + "=" * 60)
    if db_ok and deps_ok and config_ok:
        print("✅ Phase 1 verification PASSED!")
        print("=" * 60)
        print("\n🎯 Next steps:")
        print("   1. Ensure GROQ_API_KEY is set in .env")
        print("   2. Proceed to Phase 2: Core Components")
        return 0
    else:
        print("❌ Phase 1 verification FAILED")
        print("=" * 60)
        print("\n🔧 Fix the issues above before proceeding to Phase 2")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
