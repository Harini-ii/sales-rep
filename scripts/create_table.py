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

ddl = """
CREATE TABLE IF NOT EXISTS sales_hj.aircraft_images (
    id SERIAL PRIMARY KEY,
    image_id VARCHAR(50) UNIQUE NOT NULL,
    image_name VARCHAR(255) NOT NULL,
    image_url TEXT NOT NULL,
    category VARCHAR(50),
    aircraft_model VARCHAR(150),
    file_format VARCHAR(10),
    r2_key TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_aircraft_images_image_id ON sales_hj.aircraft_images(image_id);
CREATE INDEX IF NOT EXISTS idx_aircraft_images_name ON sales_hj.aircraft_images(image_name);
CREATE INDEX IF NOT EXISTS idx_aircraft_images_model ON sales_hj.aircraft_images(aircraft_model);
CREATE INDEX IF NOT EXISTS idx_aircraft_images_category ON sales_hj.aircraft_images(category);
"""

with engine.begin() as conn:
    conn.execute(text(ddl))
    print("✅ Successfully executed DDL for sales_hj.aircraft_images")

# Verify table creation
with engine.connect() as conn:
    cols = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'sales_hj' AND table_name = 'aircraft_images'
        ORDER BY ordinal_position;
    """)).fetchall()
    print("\nVerified columns in sales_hj.aircraft_images:")
    for c in cols:
        print(f"  - {c[0]}: {c[1]} (nullable: {c[2]})")
