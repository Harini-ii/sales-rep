import os
from pathlib import Path
from typing import Optional

# Path configuration
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_LOCATIONS = [
    BASE_DIR / ".env",
    BASE_DIR.parent / ".env",
    Path(".env")
]

def load_env_variables() -> None:
    """
    Lightweight .env loader that populates os.environ without requiring external dependencies.
    Existing os.environ variables take precedence.
    """
    for env_path in ENV_LOCATIONS:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip("\"'")
                            if key and key not in os.environ:
                                os.environ[key] = val
            except Exception:
                pass

load_env_variables()

# Cloudflare R2 Settings
R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "helightjet")
R2_ENDPOINT_URL: str = os.getenv(
    "R2_ENDPOINT_URL",
    "https://f91f6a555fad7eef00d6f7a144e4a5b2.r2.cloudflarestorage.com"
)
R2_ACCESS_KEY_ID: Optional[str] = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY: Optional[str] = os.getenv("R2_SECRET_ACCESS_KEY")
R2_PUBLIC_DOMAIN: Optional[str] = os.getenv("R2_PUBLIC_DOMAIN")

# PostgreSQL Database Configuration
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "hj_db")
    if db_user and db_password:
        DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
