import sys
import os
from sqlalchemy import text
sys.path.append(os.getcwd())
from app.core.database import engine

def check_user_saved_papers():
    print("🔍 Checking user_saved_papers table schema...")
    with engine.connect() as connection:
        # Check if table exists
        result = connection.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_saved_papers')"
        ))
        exists = result.fetchone()[0]
        
        if not exists:
            print("❌ user_saved_papers table does NOT exist!")
            return
        
        print("✅ user_saved_papers table exists")
        
        # Check columns
        result = connection.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'user_saved_papers'"
        ))
        columns = [f"{row[0]} ({row[1]})" for row in result.fetchall()]
        print("\nColumns:")
        for col in columns:
            print(f" - {col}")
        
        # Check if user_id column is UUID type
        result = connection.execute(text(
            "SELECT data_type FROM information_schema.columns WHERE table_name = 'user_saved_papers' AND column_name = 'user_id'"
        ))
        user_id_type = result.fetchone()
        if user_id_type:
            print(f"\n✅ user_id column type: {user_id_type[0]}")
        else:
            print("\n❌ user_id column not found!")

if __name__ == "__main__":
    check_user_saved_papers()
