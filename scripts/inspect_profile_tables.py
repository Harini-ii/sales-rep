import os
from pathlib import Path
from sqlalchemy import create_engine, text

# Load .env
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
    print("=== INSPECTING SALES / PROFILE / USER TABLES ===")
    query = text("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema IN ('admin_hj', 'sales_hj', 'customer_hj', 'public')
        ORDER BY table_schema, table_name;
    """)
    tables = conn.execute(query).fetchall()
    for s, t in tables:
        print(f"\n--- Table: {s}.{t} ---")
        cols = conn.execute(text(f"""
            SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = '{s}' AND table_name = '{t}'
            ORDER BY ordinal_position;
        """)).fetchall()
        for c in cols:
            print(f"  - {c[0]}: {c[1]}" + (f"({c[2]})" if c[2] else "") + f" | nullable: {c[3]} | default: {c[4]}")
        
        # Count rows
        cnt = conn.execute(text(f'SELECT count(*) FROM "{s}"."{t}"')).scalar()
        print(f"  Total rows: {cnt}")
        
        # Check rows safely without exposing sensitive data
        if cnt > 0:
            rows = conn.execute(text(f'SELECT * FROM "{s}"."{t}" LIMIT 5')).fetchall()
            for r in rows:
                row_dict = dict(r._mapping)
                # Mask sensitive fields
                for k in list(row_dict.keys()):
                    if any(term in k.lower() for term in ["password", "hash", "secret", "token"]):
                        val = str(row_dict[k])
                        if val.startswith("$argon2"):
                            row_dict[k] = "[ARGON2ID HASH DETECTED]"
                        elif val.startswith("$2b$") or val.startswith("$2a$"):
                            row_dict[k] = "[BCRYPT HASH DETECTED]"
                        elif val.startswith("pbkdf2:"):
                            row_dict[k] = "[PBKDF2 HASH DETECTED]"
                        elif val:
                            row_dict[k] = f"[HASH DETECTED: prefix={val[:7]}...]"
                print("   row:", row_dict)
