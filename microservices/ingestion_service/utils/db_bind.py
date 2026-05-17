"""Normalize Python values for raw SQL (sqlite3 lacks UUID/datetime adapters; Postgres is fine too)."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from typing import Any

# Works in SQLite and PostgreSQL (unlike Postgres-only now()).
SQL_CURRENT_TIMESTAMP = "CURRENT_TIMESTAMP"


def ensure_row_ids(rows: list[dict[str, Any]], *, id_key: str = "id") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        if not item.get(id_key):
            item[id_key] = uuid.uuid4()
        out.append(item)
    return out


def prepare_rows_for_db(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return bind_sqlite_rows(ensure_row_ids(rows))


def bind_sqlite_value(value: Any) -> Any:    
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, dict | list):
        return json.dumps(value)
    return value


def bind_sqlite_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: bind_sqlite_value(val) for key, val in params.items()}


def bind_sqlite_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [bind_sqlite_params(row) for row in rows]
