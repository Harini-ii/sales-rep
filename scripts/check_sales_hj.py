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
    print("Tables in sales_hj:")
    tbls = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'sales_hj';")).fetchall()
    for t in tbls:
        print(" ", t[0])
