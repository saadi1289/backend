from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class Challenge(Base):
    __tablename__ = "challenges"
    __table_args__ = (
        UniqueConstraint("pillar", "energy_level", "number", name="uq_challenges_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pillar: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    energy_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    steps: Mapped[list["ChallengeStep"]] = relationship("ChallengeStep", back_populates="challenge", cascade="all, delete-orphan")


class ChallengeStep(Base):
    __tablename__ = "challenge_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    challenge_id: Mapped[int] = mapped_column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String(1024), nullable=False)

    challenge: Mapped[Challenge] = relationship("Challenge", back_populates="steps")


class ChallengeCompletion(Base):
    __tablename__ = "challenge_completions"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_completion_user_challenge"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id: Mapped[int] = mapped_column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    pillar: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    energy_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    challenge_id: Mapped[int] = mapped_column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), index=True)
    pillar: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    energy_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    started_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    intensity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)