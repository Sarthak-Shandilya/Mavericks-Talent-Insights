"""Topper flags after scoring (ingestion worker)."""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.db_bind import SQL_CURRENT_TIMESTAMP

logger = logging.getLogger(__name__)
_TS = SQL_CURRENT_TIMESTAMP

DEFAULT_RULES = [
    ("SPARK", None, "spark_score", 5, None, 70),
    ("FOUNDATION", None, "foundation_score", 5, None, 70),
    ("STREAM", "stream_code", "composite_score", 3, None, 75),
    ("BATCH", "batch_code", "composite_score", 3, None, 75),
    ("COMPETENCY", "assigned_competency", "composite_score", 3, None, 75),
]


def _ensure_rules(db: Session) -> None:
    for tt, scope, metric, top_n, top_pct, min_score in DEFAULT_RULES:
        exists = db.execute(
            text(
                "SELECT 1 FROM topper_rules WHERE topper_type = :tt AND is_active = 1 LIMIT 1"
            ),
            {"tt": tt},
        ).scalar()
        if exists:
            continue
        db.execute(
            text(
                f"""
                INSERT INTO topper_rules
                (id, topper_type, scope_field, metric, top_n, top_percent, min_score, is_active, version, created_at)
                VALUES (:id, :tt, :scope, :metric, :top_n, :top_pct, :min_score, 1, 1, {_TS})
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "tt": tt,
                "scope": scope,
                "metric": metric,
                "top_n": top_n,
                "top_pct": top_pct,
                "min_score": min_score,
            },
        )


def compute_toppers_for_trainees(db: Session, trainee_ids: list[str] | None) -> int:
    _ensure_rules(db)
    from processors.scorer import _ensure_default_config, _composite, _fetch_assessments

    config = _ensure_default_config(db)

    if trainee_ids:
        placeholders = ",".join(f":t{i}" for i in range(len(trainee_ids)))
        params = {f"t{i}": str(tid) for i, tid in enumerate(trainee_ids)}
        trainees = db.execute(
            text(
                f"""
                SELECT t.id, t.assigned_competency, s.code AS stream_code, b.code AS batch_code
                FROM trainees t
                LEFT JOIN streams s ON t.stream_id = s.id
                LEFT JOIN batches b ON t.batch_id = b.id
                WHERE t.is_active = 1 AND t.id IN ({placeholders})
                """
            ),
            params,
        ).mappings().all()
    else:
        trainees = db.execute(
            text(
                """
                SELECT t.id, t.assigned_competency, s.code AS stream_code, b.code AS batch_code
                FROM trainees t
                LEFT JOIN streams s ON t.stream_id = s.id
                LEFT JOIN batches b ON t.batch_id = b.id
                WHERE t.is_active = 1
                """
            )
        ).mappings().all()

    rules = db.execute(
        text("SELECT * FROM topper_rules WHERE is_active = 1")
    ).mappings().all()

    created = 0
    for rule in rules:
        db.execute(
            text("DELETE FROM topper_flags WHERE topper_type = :tt"),
            {"tt": rule["topper_type"]},
        )
        groups: dict[str | None, list[tuple[str, float]]] = {}
        for t in trainees:
            tid = str(t["id"])
            assessments = _fetch_assessments(db, tid)
            metric = rule["metric"]
            if metric == "spark_score":
                spark = [a for a in assessments if a["program"] == "SPARK"]
                if not spark:
                    continue
                score = max(float(a["score"]) / float(a["max_score"]) * 100 for a in spark if float(a["max_score"]) > 0)
            elif metric == "foundation_score":
                found = [a for a in assessments if a["program"] == "FOUNDATION"]
                if not found:
                    continue
                norms = [float(a["score"]) / float(a["max_score"]) * 100 for a in found if float(a["max_score"]) > 0]
                score = sum(norms) / len(norms) if norms else 0
            else:
                comp = _composite(assessments, config["weights"])
                if comp is None:
                    continue
                score = comp
            if rule["min_score"] and score < float(rule["min_score"]):
                continue
            scope_field = rule["scope_field"]
            if scope_field == "stream_code":
                key = t["stream_code"]
            elif scope_field == "batch_code":
                key = t["batch_code"]
            elif scope_field == "assigned_competency":
                key = t["assigned_competency"]
            else:
                key = None
            groups.setdefault(key, []).append((tid, score))

        for scope_value, entries in groups.items():
            entries.sort(key=lambda x: x[1], reverse=True)
            top_n = rule["top_n"] or 10
            for rank, (tid, _) in enumerate(entries[:top_n], start=1):
                db.execute(
                    text(
                        f"""
                        INSERT INTO topper_flags
                        (id, trainee_id, topper_type, scope_value, rank, rule_id, rule_version, computed_at)
                        VALUES (:id, :tid, :tt, :scope, :rank, :rid, :rv, {_TS})
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "tid": tid,
                        "tt": rule["topper_type"],
                        "scope": scope_value,
                        "rank": rank,
                        "rid": str(rule["id"]),
                        "rv": rule["version"],
                    },
                )
                created += 1
    return created
