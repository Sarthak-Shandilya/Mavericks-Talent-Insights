"""SQLite helpers for local dev (create tables, patch columns, seed reference).

PostgreSQL: use `alembic upgrade head` instead — do not rely on these helpers.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def prepare_sqlite_for_dev(engine: Engine) -> None:
    """Create missing tables + reference seed on empty/partial local SQLite files."""
    if engine.dialect.name != "sqlite":
        return

    import models  # noqa: F401 — register ORM mappers on Base.metadata
    from models.base import Base
    from scripts.seed_reference import seed_reference_data

    with engine.connect() as conn:
        has_users = conn.execute(
            text("SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'")
        ).scalar()

    if not has_users:
        logger.warning(
            "sqlite: no users table — creating all tables and seeding reference data "
            "(run `python scripts/init_sqlite_db.py` manually if you prefer)"
        )
        Base.metadata.create_all(bind=engine)
        with Session(engine) as session:
            seed_reference_data(session)
    else:
        Base.metadata.create_all(bind=engine)

    ensure_sqlite_schema_alignment(engine)


def ensure_sqlite_schema_alignment(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM sqlite_master WHERE type='table' AND name='upload_batches'")
        ).scalar()
        if not exists:
            return
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(upload_batches)"))}
        if "file_hash" not in cols:
            conn.execute(text("ALTER TABLE upload_batches ADD COLUMN file_hash VARCHAR(128)"))
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_upload_batches_file_hash "
                    "ON upload_batches (file_hash)"
                )
            )
