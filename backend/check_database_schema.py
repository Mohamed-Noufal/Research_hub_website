"""
Check actual database schema to identify all column mismatches
"""
import sys
import os
from sqlalchemy import create_engine, text
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/paper_search"

def check_all_schemas():
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    tables_to_check = [
        'papers',
        'project_papers',
        'findings',
        'methodology_data',
        'research_gaps',
        'comparison_configs',
        'comparison_attributes',
        'synthesis_configs',
        'synthesis_cells',
        'analysis_configs'
    ]
    
    schema_info = {}
    
    for table in tables_to_check:
        print(f"\n{'='*70}")
        print(f"TABLE: {table}")
        print('='*70)
        
        result = conn.execute(text("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """), {"table_name": table})
        
        columns = result.fetchall()
        schema_info[table] = columns
        
        if columns:
            for col in columns:
                print(f"  {col[0]:<30} {col[1]:<20} ({col[2]})")
        else:
            print(f"  ⚠️ Table '{table}' does not exist!")
    
    conn.close()
    
    # Save to JSON
    schema_dict = {}
    for table, cols in schema_info.items():
        schema_dict[table] = [{"name": c[0], "type": c[1], "udt": c[2]} for c in cols]
    
    with open('database_schema.json', 'w') as f:
        json.dump(schema_dict, f, indent=2)
    
    print(f"\n{'='*70}")
    print("Schema saved to database_schema.json")
    print('='*70)

if __name__ == "__main__":
    check_all_schemas()
