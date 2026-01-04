"""
Generate embeddings for existing papers in database
Run this ONCE to backfill embeddings for papers saved before the fix
"""
import asyncio
from app.core.database import SessionLocal
from app.services.enhanced_vector_service import EnhancedVectorService

async def generate_embeddings_for_existing_papers():
    db = SessionLocal()
    vector_service = EnhancedVectorService()
    
    print("🔄 Generating embeddings for existing papers...")
    
    try:
        result = await vector_service.generate_embeddings_for_papers(
            db=db,
            batch_size=50,  # Process 50 papers at a time
            max_papers=None,  # Process ALL papers
            force_regenerate=False  # Only papers without embeddings
        )
        
        print("\n✅ COMPLETE!")
        print(f"📊 {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(generate_embeddings_for_existing_papers())
