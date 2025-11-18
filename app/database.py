from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


# Neon Postgres engine configuration optimized for Vercel serverless
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # 🔥 Required for serverless - no connection pooling
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()