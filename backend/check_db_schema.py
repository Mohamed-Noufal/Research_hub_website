"""Query detailed database schema"""
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Get all tables
print("=" * 70)
print("ALL TABLES IN DATABASE:")
print("=" * 70)
result = db.execute(text("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name
"""))
tables = [r[0] for r in result.fetchall()]
for t in tables:
    print(f"  - {t}")

print(f"\nTotal tables: {len(tables)}")

# Get column details for ALL tables
print("\n" + "=" * 70)
print("DETAILED TABLE STRUCTURES:")
print("=" * 70)

for table in tables:
    print(f"\n📄 {table}:")
    result = db.execute(text(f"""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns 
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """))
    for col in result.fetchall():
        dtype = col[1]
        if col[2]:
            dtype += f"({col[2]})"
        nullable = "NULL" if col[3] == 'YES' else "NOT NULL"
        print(f"   {col[0]}: {dtype} ({nullable})")

# Get row counts for all tables
print("\n" + "=" * 70)
print("ROW COUNTS:")
print("=" * 70)
counts = []
for table in tables:
    try:
        result = db.execute(text(f"SELECT COUNT(*) FROM \"{table}\""))
        count = result.scalar()
        counts.append((table, count))
    except Exception as e:
        counts.append((table, f"ERROR: {e}"))

# Sort by count descending
counts.sort(key=lambda x: x[1] if isinstance(x[1], int) else -1, reverse=True)
for table, count in counts:
    print(f"  {table}: {count}")

db.close()
