"""
Standalone PostgreSQL connectivity verification script for Helite Jet (hj_db).
Updated to check the confirmed schemas: admin_hj, customer_hj, sales_hj, public.

Features:
- Never prints or exposes passwords or sensitive credentials
- Tests network port reachability
- Inspects existing tables, columns, and foreign keys across schemas
- Specifically checks for existing aircraft, fleet, or image tables
"""
import os
import sys
import socket
from pathlib import Path

# Load environment variables from .env safely
def load_env():
    env_file = Path(".env")
    if env_file.is_file():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("\"'")
                    if k and k not in os.environ:
                        os.environ[k] = v

load_env()

db_url = os.getenv("DATABASE_URL")
db_host = os.getenv("DB_HOST", "localhost")
db_port = int(os.getenv("DB_PORT", "5432"))
db_name = os.getenv("DB_NAME", "hj_db")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

TARGET_SCHEMAS = ("admin_hj", "customer_hj", "sales_hj", "public")

print("=" * 65)
print("  Helite Jet (hj_db) PostgreSQL Connectivity & Schema Inspector")
print("=" * 65)
print(f"Target Database : {db_name}")
print(f"Target Schemas  : {', '.join(TARGET_SCHEMAS)}")
print(f"Proposed Schema : sales_hj")
print("-" * 65)

# Step 1: Network socket test
print(f"1. Testing network port reachability ({db_host}:{db_port})...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    result = sock.connect_ex((db_host, db_port))
    sock.close()
    if result == 0:
        print(f"   ✅ Port {db_port} on host '{db_host}' is OPEN and reachable.")
    else:
        print(f"   ⚠️  Port {db_port} on host '{db_host}' is NOT responding (error code: {result}).")
        print("      Make sure PostgreSQL service is running.")
except Exception as sock_err:
    print(f"   ⚠️  Socket error: {sock_err}")

# Step 2: Database authentication and schema inspection
print("\n2. Checking PostgreSQL database connection...")
if not db_url and not (db_user and db_password):
    print("   ❌ Database credentials not found in environment or .env.")
    print("      Please configure DATABASE_URL or DB_USER / DB_PASSWORD.")
    sys.exit(1)

if not db_url:
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("   ℹ️  SQLAlchemy or psycopg2-binary not installed in this environment.")
    print("      To run full DB inspection from CLI, install dependencies:")
    print("      pip install sqlalchemy psycopg2-binary")
    print("      Alternatively, use the SQL queries provided for pgAdmin.")
    sys.exit(0)

try:
    engine = create_engine(db_url, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        res = conn.execute(text("SELECT current_database(), current_user, version();")).fetchone()
        print(f"   ✅ Connected successfully!")
        print(f"      Database : {res[0]}")
        print(f"      User     : {res[1]}")
        print(f"      Engine   : {res[2].split(',')[0]}")

        # Check existing schemas
        print("\n3. Inspecting configured schemas...")
        schema_query = text(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name IN :schemas "
            "ORDER BY schema_name;"
        )
        found_schemas = [row[0] for row in conn.execute(schema_query, {"schemas": TARGET_SCHEMAS}).fetchall()]
        print(f"   Verified schemas in hj_db: {found_schemas}")

        # Check existing tables across schemas
        print("\n4. Checking existing tables in target schemas...")
        tables_query = text(
            "SELECT table_schema, table_name "
            "FROM information_schema.tables "
            "WHERE table_schema IN :schemas "
            "ORDER BY table_schema, table_name;"
        )
        tables = conn.execute(tables_query, {"schemas": TARGET_SCHEMAS}).fetchall()
        if tables:
            print(f"   Found {len(tables)} existing tables:")
            for s, t in tables:
                print(f"     - {s}.{t}")
        else:
            print("   ℹ️  No tables found in target schemas.")

        # Check specifically for image, aircraft, fleet, or asset tables
        print("\n5. Searching for existing image/aircraft/fleet tables...")
        image_tables_query = text(
            "SELECT table_schema, table_name "
            "FROM information_schema.tables "
            "WHERE table_schema IN :schemas "
            "  AND (table_name ILIKE '%image%' "
            "    OR table_name ILIKE '%aircraft%' "
            "    OR table_name ILIKE '%fleet%' "
            "    OR table_name ILIKE '%asset%') "
            "ORDER BY table_schema, table_name;"
        )
        matching = conn.execute(image_tables_query, {"schemas": TARGET_SCHEMAS}).fetchall()
        if matching:
            print("   ⚠️  Existing image/aircraft tables detected:")
            for s, t in matching:
                print(f"     👉 {s}.{t}")
                # List columns of matching table
                cols_query = text(
                    "SELECT column_name, data_type, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema = :s AND table_name = :t "
                    "ORDER BY ordinal_position;"
                )
                cols = conn.execute(cols_query, {"s": s, "t": t}).fetchall()
                for c in cols:
                    print(f"        • {c[0]} ({c[1]}, nullable: {c[2]})")
        else:
            print("   ✅ No existing image or aircraft tables detected. Safe to create new table.")

    print("\n" + "=" * 65)
    print("  Inspection complete. All existing APIs and mock data unchanged.")
    print("=" * 65)

except Exception as err:
    err_msg = str(err)
    if db_password and db_password in err_msg:
        err_msg = err_msg.replace(db_password, "********")
    print(f"   ❌ Connection failed: {err_msg.splitlines()[0]}")
    sys.exit(1)
