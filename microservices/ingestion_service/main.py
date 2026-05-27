from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.engine.url import make_url

from configs.settings import get_settings
from db.session import engine
from processors import process_upload
from utils.queue_clients import get_queue_client
from utils.sqlite_schema import ensure_sqlite_schema_alignment, warn_if_sqlite_missing_core_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("ingestion-service")


def _safe_database_url(url: str) -> str:
    try:
        return make_url(url).render_as_string(hide_password=True)
    except Exception:
        return "<invalid DATABASE_URL>"


def _warn_if_likely_db_mismatch(database_url: str) -> None:
    """Warn when worker appears to use its own local sqlite DB."""
    try:
        url = make_url(database_url)
    except Exception:
        return
    if url.get_backend_name() != "sqlite":
        return
    if database_url.strip() == "sqlite:///./mavericks.db":
        logger.warning(
            "worker DATABASE_URL=%s may point to ingestion_service/mavericks.db depending on cwd. "
            "Use same DB as API (commonly sqlite:///../../mavericks.db).",
            database_url,
        )
        return
    db = url.database or ""
    if db and not Path(db).is_absolute():
        logger.warning(
            "worker sqlite DATABASE_URL uses relative path '%s'; ensure it resolves to API DB file.",
            db,
        )


def _handler(message: dict) -> None:
    uid = message.get("upload_id")
    logger.info("queue: handler invoked upload_id=%s raw_keys=%s", uid, list(message.keys()))
    logger.debug("queue: full message %s", json.dumps(message))
    try:
        process_upload(message)
        logger.info("queue: handler OK upload_id=%s", uid)
    except Exception:
        logger.exception("queue: handler ERROR upload_id=%s", uid)
        raise


def main() -> None:
    settings = get_settings()
    _warn_if_likely_db_mismatch(settings.database_url)
    ensure_sqlite_schema_alignment(engine)
    warn_if_sqlite_missing_core_tables(engine)
    logger.info(
        "worker boot queue_type=%s queue_in=%s queue_done=%s storage=%s local_dir=%s db=%s",
        settings.queue_type,
        settings.queue_name_ingestion,
        settings.queue_name_ingestion_completed,
        settings.storage_type,
        settings.local_storage_dir,
        _safe_database_url(settings.database_url),
    )
    logger.info("worker: connecting queue consumer…")
    queue = get_queue_client()
    queue.consume(queue_name=settings.queue_name_ingestion, handler=_handler)


if __name__ == "__main__":
    main()
