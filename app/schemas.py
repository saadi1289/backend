from pydantic import BaseModel, EmailStr
from datetime import datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    type: str


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    token: str


class SessionCreate(BaseModel):
    challenge_id: int
    duration_seconds: int
    intensity: str | None = "MEDIUM"
    started_at: datetime | None = None
    ended_at: datetime | None = None


class SessionOut(BaseModel):
    id: int
    challenge_id: int
    pillar: str
    energy_level: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    intensity: str
    points: int


class SummaryOut(BaseModel):
    completed_count: int
    total_minutes: int
    streak_days: int
    points: int