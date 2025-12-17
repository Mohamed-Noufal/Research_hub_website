"""
Check comparison_configs table
"""
import psycopg2

conn = psycopg2.connect("dbname=paper_search user=postgres password=postgres host=localhost")
cur = conn.cursor()

print("Checking comparison_configs table...")
cur.execute("SELECT * FROM comparison_configs WHERE project_id = 1")
rows = cur.fetchall()
print(f"Rows: {len(rows)}")
for row in rows:
    print(row)

print("\nChecking table schema...")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'comparison_configs'
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
