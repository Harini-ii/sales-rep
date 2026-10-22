import os
from pathlib import Path
from sqlalchemy import create_engine, text

env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))

db_host = os.environ.get("DB_HOST")
db_port = os.environ.get("DB_PORT", "5432")
db_name = os.environ.get("DB_NAME", "hj_db")
db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")

db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(db_url)

with engine.begin() as conn:
    # 1. Revert changes made to admin_hj.sales_team_hj (remove test row id=1)
    print("Cleaning up admin_hj.sales_team_hj...")
    conn.execute(text("DELETE FROM admin_hj.sales_team_hj WHERE id = 1;"))
    print("✅ Removed id=1 from admin_hj.sales_team_hj")

    # 2. Create sales_hj.sales_team table
    print("Creating sales_hj.sales_team table...")
    ddl = """
    CREATE TABLE IF NOT EXISTS sales_hj.sales_team (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        mobile_number VARCHAR(50) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        department VARCHAR(100) DEFAULT 'Sales',
        joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_sales_team_email ON sales_hj.sales_team(email);
    """
    conn.execute(text(ddl))
    print("✅ Created sales_hj.sales_team table")

# 3. Verification
with engine.connect() as conn:
    print("\n--- Remaining in admin_hj.sales_team_hj ---")
    admin_rows = conn.execute(text("SELECT id, full_name, email FROM admin_hj.sales_team_hj;")).fetchall()
    for r in admin_rows:
        print(" ", dict(r._mapping))

    print("\n--- Columns in sales_hj.sales_team ---")
    cols = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'sales_hj' AND table_name = 'sales_team'
        ORDER BY ordinal_position;
    """)).fetchall()
    for c in cols:
        print(f"  - {c[0]}: {c[1]} (nullable: {c[2]})")
