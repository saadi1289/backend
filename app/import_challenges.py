import csv
import os
from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from .models import Challenge, ChallengeStep

def parse_duration(value: str) -> int:
    v = value.strip().lower()
    if v.endswith("minutes"):
        v = v.replace("minutes", "").strip()
    if v.endswith("minute"):
        v = v.replace("minute", "").strip()
    try:
        return int(v)
    except Exception:
        return 5

def import_csv(csv_path: str):
    Base.metadata.create_all(bind=engine)
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with SessionLocal() as db:
            for row in reader:
                pillar = row.get("Pillar", "").strip()
                energy = row.get("Energy Level", "").strip().upper()
                number = int(row.get("Challenge #", "0").strip() or 0)
                name = row.get("Challenge Name", "").strip()
                duration = parse_duration(row.get("Duration", "5 minutes"))
                description = row.get("Description", "").strip()
                steps_raw = row.get("Steps", "").strip()
                steps = [s.strip() for s in steps_raw.split("|") if s.strip()]

                existing = db.query(Challenge).filter(
                    Challenge.pillar == pillar,
                    Challenge.energy_level == energy,
                    Challenge.number == number,
                ).first()
                if existing:
                    db.query(ChallengeStep).filter(ChallengeStep.challenge_id == existing.id).delete()
                    existing.name = name
                    existing.duration_minutes = duration
                    existing.description = description
                    db.add(existing)
                    db.flush()
                    cid = existing.id
                else:
                    c = Challenge(
                        pillar=pillar,
                        energy_level=energy,
                        number=number,
                        name=name,
                        duration_minutes=duration,
                        description=description,
                    )
                    db.add(c)
                    db.flush()
                    cid = c.id
                for idx, s in enumerate(steps, start=1):
                    db.add(ChallengeStep(challenge_id=cid, order=idx, text=s))
            db.commit()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m backend.app.import_challenges <csv_path>")
        raise SystemExit(1)
    import_csv(sys.argv[1])