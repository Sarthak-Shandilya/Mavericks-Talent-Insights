"""Idempotent SQLite fixes when the DB predates ORM columns (see repo root utils/sqlite_schema.py)."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_CORE_TABLES = ("users", "upload_batches", "trainees", "streams", "training_stage_types")


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


def warn_if_sqlite_missing_core_tables(engine: Engine) -> None:
    """Worker shares the API DB file — schema must be created from repo root first."""
    if engine.dialect.name != "sqlite":
        return
    with engine.connect() as conn:
        missing = []
        for table in _CORE_TABLES:
            found = conn.execute(
                text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:t"),
                {"t": table},
            ).scalar()
            if not found:
                missing.append(table)
    if missing:
        logger.error(
            "sqlite missing tables %s — from repo root run: python scripts/init_sqlite_db.py "
            "and start API once (prepare_sqlite_for_dev). Worker DATABASE_URL must match API.",
            missing,
        )
