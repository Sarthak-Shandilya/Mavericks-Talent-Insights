"""Create all tables + seed reference rows for local SQLite (run once).

PostgreSQL: use `alembic upgrade head` instead — do not run this script.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session

from configs.settings import get_settings

import models  # noqa: F401 — register all models on Base
from models.base import Base
from scripts.seed_reference import seed_reference_data
from utils.database import engine


def main() -> None:
    settings = get_settings()
    if not settings.database_url.startswith("sqlite"):
        print("DATABASE_URL must start with sqlite for this script.")
        print("For PostgreSQL run: alembic upgrade head")
        raise SystemExit(1)
    print("Creating tables from SQLAlchemy models...")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        print("Seeding roles, training_stage_types, streams, assessment_catalog...")
        seed_reference_data(session)
    print("OK.")
    print("  DB file:", settings.database_url.replace("sqlite:///", "", 1))
    print("Next: set BOOTSTRAP_ADMIN_EMAIL + BOOTSTRAP_ADMIN_PASSWORD in .env, then:")
    print("  uvicorn main:app --reload")


if __name__ == "__main__":
    main()
