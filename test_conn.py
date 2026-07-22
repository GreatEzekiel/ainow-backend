# test_conn.py
import os
from sqlalchemy import create_engine, text

# Get DATABASE_URL or paste your Render External URL directly here inside quotes for a quick test
db_url = os.getenv("DATABASE_URL", "postgresql://ainow_db_user:wWjmYrec2ScItCPvwZdRPvPw6SgtoS2F@dpg-d9g8vrupbkes73890isg-a.oregon-postgres.render.com/ainow_db") 

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://ainow_db_user:wWjmYrec2ScItCPvwZdRPvPw6SgtoS2F@dpg-d9g8vrupbkes73890isg-a.oregon-postgres.render.com/ainow_db", 1)

print(f"Attempting connection to: {db_url.split('@')[-1] if '@' in db_url else 'Local DB'}...")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1;"))
        print("✅ SUCCESS: Database connected successfully!")
except Exception as e:
    print("❌ CONNECTION FAILED! Here is the exact error:\n")
    print(e)