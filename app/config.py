import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", "10080"))

def _normalize_pg_url(url: str) -> str:
    """Normalize PostgreSQL URL for SQLAlchemy with psycopg driver"""
    u = url
    # Add psycopg driver if not present
    if "+psycopg" not in u and u.startswith("postgres"):
        u = u.replace("postgres://", "postgresql+psycopg://").replace("postgresql://", "postgresql+psycopg://")
    # Ensure SSL mode is required for Neon
    if "sslmode=" not in u and ".neon.tech" in u:
        sep = "&" if "?" in u else "?"
        u = f"{u}{sep}sslmode=require"
    return u

# Get DATABASE_URL from environment
_database_url = os.environ.get("DATABASE_URL")

if not _database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Please set it to your Neon Postgres connection string."
    )

DATABASE_URL = _normalize_pg_url(_database_url)

def access_token_expiry() -> timedelta:
    return timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

def refresh_token_expiry() -> timedelta:
    return timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)