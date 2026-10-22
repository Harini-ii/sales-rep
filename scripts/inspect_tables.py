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
engine = create_engine(db_url, connect_args={"connect_timeout": 10})

with engine.connect() as conn:
    print("=== CONNECTED TO hj_db ===")
    
    # 1. Check all tables across schemas
    tables_query = text("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema IN ('admin_hj', 'public', 'sales_hj', 'customer_hj')
        ORDER BY table_schema, table_name;
    """)
    tables = conn.execute(tables_query).fetchall()
    print("\n--- ALL TABLES IN TARGET SCHEMAS ---")
    for s, t in tables:
        print(f"  {s}.{t}")

    # 2. Inspect admin_hj.aircraft and public.aircraft columns and any sales_hj tables
    inspect_query = text("""
        SELECT table_schema, table_name, column_name, data_type, character_maximum_length, is_nullable, column_default
        FROM information_schema.columns
        WHERE (table_schema = 'admin_hj' AND table_name = 'aircraft')
           OR (table_schema = 'public' AND table_name = 'aircraft')
           OR (table_schema = 'sales_hj')
        ORDER BY table_schema, table_name, ordinal_position;
    """)
    cols = conn.execute(inspect_query).fetchall()
    print("\n--- COLUMNS FOR TARGET TABLES ---")
    curr_tbl = None
    for row in cols:
        tbl = f"{row[0]}.{row[1]}"
        if tbl != curr_tbl:
            curr_tbl = tbl
            print(f"\nTable: {curr_tbl}")
        print(f"  - {row[2]}: {row[3]}" + (f"({row[4]})" if row[4] else "") + f" | nullable: {row[5]}" + (f" | default: {row[6]}" if row[6] else ""))

    # 3. Check for any image columns across all tables in admin_hj, sales_hj, public
    image_cols_query = text("""
        SELECT table_schema, table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema IN ('admin_hj', 'sales_hj', 'public', 'customer_hj')
          AND (column_name ILIKE '%image%' OR column_name ILIKE '%photo%' OR column_name ILIKE '%url%' OR column_name ILIKE '%media%')
        ORDER BY table_schema, table_name, ordinal_position;
    """)
    img_cols = conn.execute(image_cols_query).fetchall()
    print("\n--- IMAGE/MEDIA RELATED COLUMNS ACROSS ALL TABLES ---")
    for ic in img_cols:
        print(f"  {ic[0]}.{ic[1]}.{ic[2]} ({ic[3]})")

    print("\n--- SAMPLE ROWS IN admin_hj.aircraft ---")
    rows = conn.execute(text("SELECT id, model, type, seating, image FROM admin_hj.aircraft LIMIT 10;")).fetchall()
    for r in rows:
        print(f"  ID: {r[0]} | Model: {r[1]} | Type: {r[2]} | Seating: {r[3]} | Image: {r[4]}")
    
    cnt_admin = conn.execute(text("SELECT count(*) FROM admin_hj.aircraft;")).scalar()
    cnt_public = conn.execute(text("SELECT count(*) FROM public.aircraft;")).scalar()
    print(f"\nTotal in admin_hj.aircraft: {cnt_admin}")
    print(f"Total in public.aircraft: {cnt_public}")
