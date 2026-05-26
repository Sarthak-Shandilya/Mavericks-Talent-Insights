"""Performance scoring and classification (BRD §7.4, §9)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.automation import ClassificationOverride, PerformanceClassification, ScoringConfig
from models.enums import PerformanceBand
from models.trainee import Assessment, Trainee

DEFAULT_WEIGHTS: dict[str, float] = {
    "SPARK": 0.15,
    "FOUNDATION": 0.25,
    "TECHNICAL": 0.20,
    "PROJECT": 0.15,
    "SOFT_SKILL": 0.10,
    "CODING_TEST": 0.15,
}


def get_active_scoring_config(db: Session) -> ScoringConfig | None:
    return db.execute(
        select(ScoringConfig).where(ScoringConfig.is_active.is_(True)).limit(1)
    ).scalar_one_or_none()


def ensure_default_scoring_config(db: Session) -> ScoringConfig:
    existing = get_active_scoring_config(db)
    if existing:
        return existing
    config = ScoringConfig(
        version=1,
        is_active=True,
        weights=DEFAULT_WEIGHTS,
        high_threshold=Decimal("75"),
        average_threshold=Decimal("50"),
    )
    db.add(config)
    db.flush()
    return config


def _best_normalized_by_program(assessments: list[Assessment]) -> dict[str, list[float]]:
    """Best normalized score (0-100) per assessment_code, grouped by program."""
    by_code: dict[str, tuple[str, float]] = {}
    for a in assessments:
        if not a.max_score or float(a.max_score) <= 0:
            continue
        norm = float(a.score) / float(a.max_score) * 100.0
        key = a.assessment_code
        if key not in by_code or norm > by_code[key][1]:
            by_code[key] = (a.program, norm)
    by_program: dict[str, list[float]] = {}
    for program, norm in by_code.values():
        by_program.setdefault(program, []).append(norm)
    return by_program


def compute_composite_score(assessments: list[Assessment], weights: dict) -> float | None:
    by_program = _best_normalized_by_program(assessments)
    if not by_program:
        return None
    total_weight = 0.0
    weighted_sum = 0.0
    for program, scores in by_program.items():
        w = float(weights.get(program, weights.get(program.upper(), 0)))
        if w <= 0:
            continue
        program_avg = sum(scores) / len(scores)
        weighted_sum += program_avg * w
        total_weight += w
    if total_weight <= 0:
        return None
    return round(weighted_sum / total_weight, 4)


def score_to_band(score: float, high_threshold: float, average_threshold: float) -> str:
    if score >= high_threshold:
        return PerformanceBand.HIGH.value
    if score >= average_threshold:
        return PerformanceBand.AVERAGE.value
    return PerformanceBand.LOW.value


def _active_override(db: Session, trainee_id: uuid.UUID) -> ClassificationOverride | None:
    now = datetime.now(UTC)
    overrides = db.execute(
        select(ClassificationOverride)
        .where(ClassificationOverride.trainee_id == trainee_id)
        .order_by(ClassificationOverride.created_at.desc())
    ).scalars().all()
    for o in overrides:
        if o.expires_at is None or o.expires_at > now:
            return o
    return None


def classify_trainee(
    db: Session,
    trainee_id: uuid.UUID,
    config: ScoringConfig | None = None,
) -> PerformanceClassification | None:
    config = config or ensure_default_scoring_config(db)
    assessments = db.execute(
        select(Assessment).where(Assessment.trainee_id == trainee_id)
    ).scalars().all()
    composite = compute_composite_score(assessments, config.weights)
    if composite is None:
        return None

    override = _active_override(db, trainee_id)
    if override:
        band = override.override_classification
    else:
        band = score_to_band(
            composite,
            float(config.high_threshold),
            float(config.average_threshold),
        )

    existing = db.execute(
        select(PerformanceClassification).where(
            PerformanceClassification.trainee_id == trainee_id
        )
    ).scalar_one_or_none()

    if existing:
        existing.classification = band
        existing.composite_score = composite
        existing.scoring_config_id = config.id
        existing.computed_at = datetime.now(UTC)
        pc = existing
    else:
        pc = PerformanceClassification(
            trainee_id=trainee_id,
            classification=band,
            composite_score=composite,
            scoring_config_id=config.id,
            computed_at=datetime.now(UTC),
        )
        db.add(pc)
    db.flush()
    return pc


def compute_classifications_for_trainees(
    db: Session,
    trainee_ids: list[uuid.UUID | str],
) -> int:
    if not trainee_ids:
        return 0
    config = ensure_default_scoring_config(db)
    count = 0
    for tid in trainee_ids:
        uid = tid if isinstance(tid, uuid.UUID) else uuid.UUID(str(tid))
        if classify_trainee(db, uid, config):
            count += 1
    return count


def recompute_all_classifications(db: Session) -> int:
    trainee_ids = db.execute(select(Trainee.id)).scalars().all()
    return compute_classifications_for_trainees(db, list(trainee_ids))
