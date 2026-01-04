from sqlalchemy import text
from app.core.database import SessionLocal

db = SessionLocal()

# Search for "Attention is All You Need"
result = db.execute(text("""
    SELECT id, title, authors, category, embedding IS NOT NULL as has_embedding
    FROM papers 
    WHERE LOWER(title) LIKE '%attention is all you need%' 
       OR LOWER(title) LIKE '%attention is all u need%'
    LIMIT 10
""")).fetchall()

print(f'\n{"="*70}')
print(f'🔍 Searching for "Attention is All You Need" paper...')
print(f'{"="*70}\n')

if result:
    print(f'✅ Found {len(result)} matching paper(s):\n')
    for r in result:
        print(f'ID: {r[0]}')
        print(f'Title: {r[1]}')
        print(f'Authors: {r[2][:100] if r[2] else "None"}...')
        print(f'Category: {r[3]}')
        print(f'Has Embedding: {"✅ YES" if r[4] else "❌ NO"}')
        print(f'-' * 70)
else:
    print('❌ No papers found matching "Attention is All You Need"')
    
# Get overall stats
total = db.execute(text('SELECT COUNT(*) FROM papers')).scalar()
with_emb = db.execute(text('SELECT COUNT(*) FROM papers WHERE embedding IS NOT NULL')).scalar()
ai_cs = db.execute(text("SELECT COUNT(*) FROM papers WHERE category = 'ai_cs'")).scalar()

print(f'\n{"="*70}')
print('📊 Database Statistics:')
print(f'{"="*70}')
print(f'Total papers: {total}')
print(f'With embeddings: {with_emb} ({with_emb/total*100:.1f}%)')
print(f'AI/CS category: {ai_cs}')
print(f'{"="*70}\n')

db.close()
