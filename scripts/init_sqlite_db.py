"""Create all tables + seed reference rows for local SQLite (run once).

PostgreSQL: use `alembic upgrade head` instead — do not run this script.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from configs.settings import get_settings
from utils.database import engine
from utils.sqlite_schema import prepare_sqlite_for_dev


def main() -> None:
    settings = get_settings()
    if not settings.database_url.startswith("sqlite"):
        print("DATABASE_URL must start with sqlite for this script.")
        print("For PostgreSQL run: alembic upgrade head")
        raise SystemExit(1)
    print("Preparing SQLite (tables + reference seed + column patches)...")
    prepare_sqlite_for_dev(engine)
    print("OK.")
    print("  DB file:", settings.database_url.replace("sqlite:///", "", 1))
    print("Next: set BOOTSTRAP_ADMIN_EMAIL + BOOTSTRAP_ADMIN_PASSWORD in .env, then:")
    print("  uvicorn main:app --reload")


if __name__ == "__main__":
    main()
