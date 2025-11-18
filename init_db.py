"""
Database initialization script for Neon Postgres
Run this once to create all tables in your Neon database
"""
from app.database import Base, engine
from app.models import User, Challenge, ChallengeStep, ChallengeCompletion, Session

def init_database():
    """Create all tables in the database"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    print("\nTables created:")
    print("  - users")
    print("  - challenges")
    print("  - challenge_steps")
    print("  - challenge_completions")
    print("  - sessions")

if __name__ == "__main__":
    init_database()
