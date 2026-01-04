"""
Generate embedding for specific paper ID
"""
import asyncio
from app.core.database import SessionLocal
from app.services.enhanced_vector_service import EnhancedVectorService

def main():
    db = SessionLocal()
    vector_service = EnhancedVectorService()
    
    # Generate embedding for paper 1977
    asyncio.run(
        vector_service.generate_embeddings_for_papers(
            db=db,
            batch_size=1,
            max_papers=1000,  # Process all without embeddings
            force_regenerate=False
        )
    )
    
    print("✅ Embedding generation complete!")
    db.close()

if __name__ == "__main__":
    main()
