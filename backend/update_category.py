from sqlalchemy import text
from app.core.database import SessionLocal

db = SessionLocal()

# Update category for paper 1977
db.execute(text("UPDATE papers SET category = 'ai_cs' WHERE id = 1977"))
db.commit()

# Verify
result = db.execute(text("SELECT id, title, category, embedding IS NOT NULL FROM papers WHERE id = 1977")).fetchone()

print(f"\n✅ Paper 1977 Updated:")
print(f"ID: {result[0]}")
print(f"Title: {result[1]}")
print(f"Category: {result[2]}")
print(f"Has Embedding: {result[3]}")

db.close()
