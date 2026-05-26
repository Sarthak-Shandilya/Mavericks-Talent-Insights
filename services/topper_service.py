"""Topper identification engine (BRD §7.5)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from models.automation import TopperFlag, TopperRule
from models.enums import TopperType
from models.trainee import Assessment, Batch, Trainee
from services.scoring_service import compute_composite_score, ensure_default_scoring_config

DEFAULT_TOPPER_RULES: list[dict] = [
    {"topper_type": TopperType.SPARK.value, "scope_field": None, "metric": "spark_score", "top_n": 5, "top_percent": None, "min_score": Decimal("70")},
    {"topper_type": TopperType.FOUNDATION.value, "scope_field": None, "metric": "foundation_score", "top_n": 5, "top_percent": None, "min_score": Decimal("70")},
    {"topper_type": TopperType.STREAM.value, "scope_field": "stream_code", "metric": "composite_score", "top_n": 3, "top_percent": None, "min_score": Decimal("75")},
    {"topper_type": TopperType.BATCH.value, "scope_field": "batch_code", "metric": "composite_score", "top_n": 3, "top_percent": None, "min_score": Decimal("75")},
    {"topper_type": TopperType.COMPETENCY.value, "scope_field": "assigned_competency", "metric": "composite_score", "top_n": 3, "top_percent": None, "min_score": Decimal("75")},
]


def ensure_default_topper_rules(db: Session) -> None:
    for spec in DEFAULT_TOPPER_RULES:
        exists = db.execute(
            select(TopperRule.id).where(
                TopperRule.topper_type == spec["topper_type"],
                TopperRule.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if exists:
            continue
        db.add(
            TopperRule(
                topper_type=spec["topper_type"],
                scope_field=spec["scope_field"],
                metric=spec["metric"],
                top_n=spec["top_n"],
                top_percent=spec["top_percent"],
                min_score=spec["min_score"],
                is_active=True,
                version=1,
            )
        )
    db.flush()


def _spark_score(assessments: list[Assessment]) -> float | None:
    spark = [a for a in assessments if a.program == "SPARK"]
    if not spark:
        return None
    norms = []
    for a in spark:
        if float(a.max_score) > 0:
            norms.append(float(a.score) / float(a.max_score) * 100)
    return max(norms) if norms else None


def _foundation_score(assessments: list[Assessment]) -> float | None:
    found = [a for a in assessments if a.program == "FOUNDATION"]
    if not found:
        return None
    by_code: dict[str, float] = {}
    for a in found:
        if float(a.max_score) <= 0:
            continue
        norm = float(a.score) / float(a.max_score) * 100
        if a.assessment_code not in by_code or norm > by_code[a.assessment_code]:
            by_code[a.assessment_code] = norm
    if not by_code:
        return None
    return sum(by_code.values()) / len(by_code)


def _metric_value(metric: str, trainee: Trainee, assessments: list[Assessment], config_weights: dict) -> float | None:
    if metric == "spark_score":
        return _spark_score(assessments)
    if metric == "foundation_score":
        return _foundation_score(assessments)
    return compute_composite_score(assessments, config_weights)


def _scope_key(trainee: Trainee, scope_field: str | None) -> str | None:
    if not scope_field:
        return None
    if scope_field == "stream_code":
        return trainee.stream.code if trainee.stream else None
    if scope_field == "batch_code":
        return trainee.batch.code if trainee.batch else None
    if scope_field == "assigned_competency":
        return trainee.assigned_competency
    return None


def compute_toppers_for_trainees(
    db: Session,
    trainee_ids: list[uuid.UUID | str] | None = None,
) -> int:
    ensure_default_topper_rules(db)
    config = ensure_default_scoring_config(db)
    rules = db.execute(
        select(TopperRule).where(TopperRule.is_active.is_(True))
    ).scalars().all()
    if not rules:
        return 0

    q = select(Trainee).options(
        joinedload(Trainee.assessments),
        joinedload(Trainee.stream),
        joinedload(Trainee.batch),
    ).where(Trainee.is_active.is_(True))
    if trainee_ids:
        ids = [tid if isinstance(tid, uuid.UUID) else uuid.UUID(str(tid)) for tid in trainee_ids]
        q = q.where(Trainee.id.in_(ids))
    trainees = db.execute(q).unique().scalars().all()

    flags_created = 0
    for rule in rules:
        if rule.topper_type in (TopperType.SPARK.value, TopperType.FOUNDATION.value):
            db.execute(
                delete(TopperFlag).where(TopperFlag.topper_type == rule.topper_type)
            )
        else:
            db.execute(delete(TopperFlag).where(TopperFlag.topper_type == rule.topper_type))

        groups: dict[str | None, list[tuple[Trainee, float]]] = {}
        for t in trainees:
            score = _metric_value(rule.metric, t, list(t.assessments), config.weights)
            if score is None:
                continue
            if rule.min_score is not None and score < float(rule.min_score):
                continue
            key = _scope_key(t, rule.scope_field)
            groups.setdefault(key, []).append((t, score))

        for scope_value, entries in groups.items():
            entries.sort(key=lambda x: x[1], reverse=True)
            top_n = rule.top_n or 10
            if rule.top_percent:
                top_n = max(1, int(len(entries) * float(rule.top_percent) / 100))
            for rank, (t, _) in enumerate(entries[:top_n], start=1):
                db.add(
                    TopperFlag(
                        trainee_id=t.id,
                        topper_type=rule.topper_type,
                        scope_value=scope_value,
                        rank=rank,
                        rule_id=rule.id,
                        rule_version=rule.version,
                        computed_at=datetime.now(UTC),
                    )
                )
                flags_created += 1
    db.flush()
    return flags_created


def recompute_all_toppers(db: Session) -> int:
    return compute_toppers_for_trainees(db, None)
