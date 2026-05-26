"""Performance classification after assessment ingestion (raw SQL for worker)."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.db_bind import SQL_CURRENT_TIMESTAMP

logger = logging.getLogger(__name__)

_TS = SQL_CURRENT_TIMESTAMP

DEFAULT_WEIGHTS = {
    "SPARK": 0.15,
    "FOUNDATION": 0.25,
    "TECHNICAL": 0.20,
    "PROJECT": 0.15,
    "SOFT_SKILL": 0.10,
    "CODING_TEST": 0.15,
}


def _ensure_default_config(db: Session) -> dict:
    row = db.execute(
        text("SELECT id, weights, high_threshold, average_threshold FROM scoring_configs WHERE is_active = 1 LIMIT 1")
    ).mappings().first()
    if row:
        weights = row["weights"]
        if isinstance(weights, str):
            weights = json.loads(weights)
        return {
            "id": str(row["id"]),
            "weights": weights,
            "high_threshold": float(row["high_threshold"]),
            "average_threshold": float(row["average_threshold"]),
        }
    config_id = str(uuid.uuid4())
    db.execute(
        text(
            f"""
            INSERT INTO scoring_configs (id, version, is_active, weights, high_threshold, average_threshold, created_at)
            VALUES (:id, 1, 1, :weights, 75, 50, {_TS})
            """
        ),
        {"id": config_id, "weights": json.dumps(DEFAULT_WEIGHTS)},
    )
    return {
        "id": config_id,
        "weights": DEFAULT_WEIGHTS,
        "high_threshold": 75.0,
        "average_threshold": 50.0,
    }


def _fetch_assessments(db: Session, trainee_id: str) -> list[dict]:
    return db.execute(
        text(
            """
            SELECT program, assessment_code, score, max_score
            FROM assessments WHERE trainee_id = :tid
            """
        ),
        {"tid": trainee_id},
    ).mappings().all()


def _composite(assessments: list[dict], weights: dict) -> float | None:
    by_code: dict[str, tuple[str, float]] = {}
    for a in assessments:
        mx = float(a["max_score"] or 0)
        if mx <= 0:
            continue
        norm = float(a["score"]) / mx * 100.0
        code = a["assessment_code"]
        prog = a["program"]
        if code not in by_code or norm > by_code[code][1]:
            by_code[code] = (prog, norm)
    by_program: dict[str, list[float]] = {}
    for prog, norm in by_code.values():
        by_program.setdefault(prog, []).append(norm)
    if not by_program:
        return None
    total_w = 0.0
    weighted = 0.0
    for prog, scores in by_program.items():
        w = float(weights.get(prog, 0))
        if w <= 0:
            continue
        weighted += (sum(scores) / len(scores)) * w
        total_w += w
    if total_w <= 0:
        return None
    return round(weighted / total_w, 4)


def _band(score: float, high: float, avg: float) -> str:
    if score >= high:
        return "HIGH"
    if score >= avg:
        return "AVERAGE"
    return "LOW"


def _active_override(db: Session, trainee_id: str) -> str | None:
    row = db.execute(
        text(
            """
            SELECT override_classification FROM classification_overrides
            WHERE trainee_id = :tid
            AND (expires_at IS NULL OR expires_at > :now)
            ORDER BY created_at DESC LIMIT 1
            """
        ),
        {"tid": trainee_id, "now": datetime.now(UTC).isoformat()},
    ).mappings().first()
    return row["override_classification"] if row else None


def compute_classifications_for_trainees(db: Session, trainee_ids: list[str]) -> int:
    if not trainee_ids:
        return 0
    config = _ensure_default_config(db)
    count = 0
    for tid in trainee_ids:
        assessments = _fetch_assessments(db, str(tid))
        composite = _composite(assessments, config["weights"])
        if composite is None:
            continue
        override = _active_override(db, str(tid))
        band = override or _band(composite, config["high_threshold"], config["average_threshold"])
        existing = db.execute(
            text("SELECT id FROM performance_classifications WHERE trainee_id = :tid"),
            {"tid": str(tid)},
        ).scalar()
        if existing:
            db.execute(
                text(
                    f"""
                    UPDATE performance_classifications
                    SET classification = :band, composite_score = :score,
                        scoring_config_id = :cfg, computed_at = {_TS}
                    WHERE trainee_id = :tid
                    """
                ),
                {"band": band, "score": composite, "cfg": config["id"], "tid": str(tid)},
            )
        else:
            db.execute(
                text(
                    f"""
                    INSERT INTO performance_classifications
                    (id, trainee_id, classification, composite_score, scoring_config_id, computed_at)
                    VALUES (:id, :tid, :band, :score, :cfg, {_TS})
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "tid": str(tid),
                    "band": band,
                    "score": composite,
                    "cfg": config["id"],
                },
            )
        count += 1
    return count
