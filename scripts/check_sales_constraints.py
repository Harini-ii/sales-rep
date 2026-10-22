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

with engine.connect() as conn:
    print("Constraints on admin_hj.sales_team_hj:")
    c_query = text("""
        SELECT tc.constraint_name, tc.constraint_type, kcu.column_name
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'admin_hj' AND tc.table_name = 'sales_team_hj';
    """)
    for row in conn.execute(c_query).fetchall():
        print(f"  {row[0]} ({row[1]}) -> column: {row[2]}")
