from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timedelta

from .database import Base, engine, get_db
from .models import User, Challenge, ChallengeStep, ChallengeCompletion
from .models import Session
from .schemas import UserCreate, UserOut, Token, LoginRequest, RefreshRequest, SessionCreate, SessionOut, SummaryOut
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="CorpFinity Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=Token)
def register(user_in: UserCreate, db: DBSession = Depends(get_db)):
    existing = db.query(User).filter((User.email == user_in.email) | (User.username == user_in.username)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access = create_access_token(user.email)
    refresh = create_refresh_token(user.email)
    return Token(access_token=access, refresh_token=refresh)


@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access = create_access_token(user.email)
    refresh = create_refresh_token(user.email)
    return Token(access_token=access, refresh_token=refresh)


@app.post("/auth/refresh", response_model=Token)
def refresh(body: RefreshRequest, db: DBSession = Depends(get_db)):
    from .auth import decode_token, create_access_token, create_refresh_token

    payload = decode_token(body.token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    subject = payload.get("sub")
    access = create_access_token(subject)
    refresh = create_refresh_token(subject)
    return Token(access_token=access, refresh_token=refresh)


@app.get("/auth/me", response_model=UserOut)
def me(token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    return UserOut(id=user.id, username=user.username, email=user.email)
@app.get("/challenges")
def list_challenges(pillar: str | None = None, energy_level: str | None = None, db: DBSession = Depends(get_db)):
    q = db.query(Challenge)
    if pillar:
        q = q.filter(Challenge.pillar == pillar)
    if energy_level:
        q = q.filter(Challenge.energy_level == energy_level)
    items = q.order_by(Challenge.pillar, Challenge.energy_level, Challenge.number).all()
    out = []
    for c in items:
        steps = db.query(ChallengeStep).filter(ChallengeStep.challenge_id == c.id).order_by(ChallengeStep.order).all()
        out.append({
            "id": c.id,
            "pillar": c.pillar,
            "energy_level": c.energy_level,
            "number": c.number,
            "name": c.name,
            "duration_minutes": c.duration_minutes,
            "description": c.description,
            "steps": [s.text for s in steps],
        })
    return {"items": out}


@app.get("/challenges/next")
def next_challenge(pillar: str, energy_level: str, token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    challenges = db.query(Challenge).filter(
        Challenge.pillar == pillar,
        Challenge.energy_level == energy_level,
    ).order_by(Challenge.number).all()
    if not challenges:
        return {"item": None}
    completed_ids = {
        c.challenge_id for c in db.query(ChallengeCompletion).filter(
            ChallengeCompletion.user_id == user.id,
            ChallengeCompletion.pillar == pillar,
            ChallengeCompletion.energy_level == energy_level,
        ).all()
    }
    choice = None
    for c in challenges:
        if c.id not in completed_ids:
            choice = c
            break
    if choice is None:
        db.query(ChallengeCompletion).filter(
            ChallengeCompletion.user_id == user.id,
            ChallengeCompletion.pillar == pillar,
            ChallengeCompletion.energy_level == energy_level,
        ).delete()
        db.commit()
        choice = challenges[0]
    steps = db.query(ChallengeStep).filter(ChallengeStep.challenge_id == choice.id).order_by(ChallengeStep.order).all()
    return {
        "item": {
            "id": choice.id,
            "pillar": choice.pillar,
            "energy_level": choice.energy_level,
            "number": choice.number,
            "name": choice.name,
            "duration_minutes": choice.duration_minutes,
            "description": choice.description,
            "steps": [s.text for s in steps],
        }
    }


@app.post("/challenges/{challenge_id}/complete")
def complete_challenge(challenge_id: int, token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    c = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Challenge not found")
    existing = db.query(ChallengeCompletion).filter(
        ChallengeCompletion.user_id == user.id,
        ChallengeCompletion.challenge_id == challenge_id,
    ).first()
    if not existing:
        db.add(ChallengeCompletion(
            user_id=user.id,
            challenge_id=challenge_id,
            pillar=c.pillar,
            energy_level=c.energy_level,
        ))
        db.commit()
    return {"status": "ok"}


def _points_for(duration_seconds: int, intensity: str | None) -> int:
    base = max(duration_seconds // 60, 1)
    mult = 2
    if intensity:
        v = intensity.upper()
        if v == "LOW":
            mult = 1
        elif v == "MEDIUM":
            mult = 2
        elif v == "HIGH":
            mult = 3
    return base * mult


@app.post("/sessions", response_model=SessionOut)
def create_session(body: SessionCreate, token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    c = db.query(Challenge).filter(Challenge.id == body.challenge_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Challenge not found")
    points = _points_for(body.duration_seconds, body.intensity)
    started = body.started_at or datetime.utcnow()
    ended = body.ended_at or datetime.utcnow()
    s = Session(
        user_id=user.id,
        challenge_id=c.id,
        pillar=c.pillar,
        energy_level=c.energy_level,
        started_at=started,
        ended_at=ended,
        duration_seconds=body.duration_seconds,
        intensity=(body.intensity or "MEDIUM").upper(),
        points=points,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return SessionOut(
        id=s.id,
        challenge_id=s.challenge_id,
        pillar=s.pillar,
        energy_level=s.energy_level,
        started_at=s.started_at,
        ended_at=s.ended_at,
        duration_seconds=s.duration_seconds,
        intensity=s.intensity,
        points=s.points,
    )


@app.get("/activity/recent")
def recent_activity(limit: int = 20, token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    items = db.query(Session).filter(Session.user_id == user.id).order_by(Session.started_at.desc()).limit(limit).all()
    out = []
    for s in items:
        out.append({
            "id": s.id,
            "challenge_id": s.challenge_id,
            "title": db.query(Challenge).filter(Challenge.id == s.challenge_id).first().name,
            "started_at": s.started_at,
            "duration_minutes": s.duration_seconds // 60,
            "intensity": s.intensity,
            "points": s.points,
        })
    return {"items": out}


@app.get("/progress/summary", response_model=SummaryOut)
def progress_summary(token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    completed_count = db.query(ChallengeCompletion).filter(ChallengeCompletion.user_id == user.id).count()
    sessions = db.query(Session).filter(Session.user_id == user.id).all()
    total_minutes = sum(s.duration_seconds for s in sessions) // 60
    points = sum(s.points for s in sessions)
    dates = sorted({s.started_at.date() for s in sessions}, reverse=True)
    streak = 0
    if dates:
        cur = datetime.utcnow().date()
        seen = set(dates)
        while cur in seen:
            streak += 1
            cur = cur.fromordinal(cur.toordinal() - 1)
    return SummaryOut(completed_count=completed_count, total_minutes=total_minutes, streak_days=streak, points=points)


@app.get("/progress/breakdown")
def progress_breakdown(token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    by_pillar = {}
    sessions = db.query(Session).filter(Session.user_id == user.id).all()
    total_min = 0
    for s in sessions:
        m = s.duration_seconds // 60
        total_min += m
        p = s.pillar
        if p not in by_pillar:
            by_pillar[p] = {"sessions": 0, "minutes": 0}
        by_pillar[p]["sessions"] += 1
        by_pillar[p]["minutes"] += m
    items = []
    for pillar, agg in by_pillar.items():
        minutes = agg["minutes"]
        percentage = 0
        if total_min > 0:
            percentage = int((minutes * 100) / total_min)
        items.append({
            "pillar": pillar,
            "sessions": agg["sessions"],
            "minutes": minutes,
            "percentage": percentage,
        })
    return {"items": items}


@app.get("/progress/calendar")
def progress_calendar(month: str | None = None, token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    if month:
        try:
            year, mon = [int(x) for x in month.split("-")]
        except Exception:
            year, mon = datetime.utcnow().year, datetime.utcnow().month
    else:
        year, mon = datetime.utcnow().year, datetime.utcnow().month
    items = {}
    sessions = db.query(Session).filter(Session.user_id == user.id).all()
    for s in sessions:
        dt = s.started_at
        if dt.year == year and dt.month == mon:
            key = dt.day
            items[key] = items.get(key, 0) + (s.duration_seconds // 60)
    out = []
    for day in range(1, 32):
        try:
            d = datetime(year, mon, day)
        except ValueError:
            break
        mins = items.get(day, 0)
        activity = 0
        if mins > 0 and mins < 20:
            activity = 1
        elif mins >= 20:
            activity = 2
        out.append({"date": d.date().isoformat(), "activity": activity})
    return {"items": out}


@app.get("/progress/weekly")
def progress_weekly(token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    today = datetime.utcnow().date()
    start = today - timedelta(days=today.weekday())
    counts = {}
    max_count = 0
    for i in range(7):
        d = start + timedelta(days=i)
        c = db.query(Session).filter(Session.user_id == user.id, Session.started_at >= datetime(d.year, d.month, d.day), Session.started_at < datetime(d.year, d.month, d.day) + timedelta(days=1)).count()
        counts[d] = c
        if c > max_count:
            max_count = c
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    items = []
    for i in range(7):
        d = start + timedelta(days=i)
        c = counts.get(d, 0)
        ratio = 0.0 if max_count == 0 else round(c / max_count, 2)
        items.append({"day": days[i], "sessions": c, "ratio": ratio})
    return {"items": items}


@app.get("/progress/monthly")
def progress_monthly(token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    today = datetime.utcnow().date()
    year, mon = today.year, today.month
    days_in_month = 0
    for day in range(1, 32):
        try:
            datetime(year, mon, day)
            days_in_month = day
        except ValueError:
            break
    chunks = (days_in_month + 6) // 7
    items = []
    max_count = 0
    counts = []
    for i in range(chunks):
        start_day = 1 + i * 7
        start_dt = datetime(year, mon, start_day)
        if i == chunks - 1:
            end_dt = datetime(year, mon, days_in_month) + timedelta(days=1)
        else:
            end_dt = start_dt + timedelta(days=7)
        c = db.query(Session).filter(
            Session.user_id == user.id,
            Session.started_at >= start_dt,
            Session.started_at < end_dt,
        ).count()
        counts.append(c)
        if c > max_count:
            max_count = c
    for i in range(chunks):
        c = counts[i]
        ratio = 0.0 if max_count == 0 else round(c / max_count, 2)
        items.append({"day": f"W{i+1}", "sessions": c, "ratio": ratio})
    return {"items": items}


@app.get("/progress/yearly")
def progress_yearly(token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)):
    user = get_current_user(token, db)
    year = datetime.utcnow().year
    items = []
    max_count = 0
    counts = []
    for m in range(1, 13):
        start_dt = datetime(year, m, 1)
        next_month = (start_dt.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_dt = next_month
        c = db.query(Session).filter(
            Session.user_id == user.id,
            Session.started_at >= start_dt,
            Session.started_at < end_dt,
        ).count()
        counts.append(c)
        if c > max_count:
            max_count = c
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i in range(12):
        c = counts[i]
        ratio = 0.0 if max_count == 0 else round(c / max_count, 2)
        items.append({"day": months[i], "sessions": c, "ratio": ratio})
    return {"items": items}


