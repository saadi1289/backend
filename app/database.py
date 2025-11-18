from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


# Neon Postgres engine configuration optimized for Vercel serverless
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,  # Smaller pool for serverless
    max_overflow=10,
    pool_recycle=300,  # Recycle connections after 5 minutes
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