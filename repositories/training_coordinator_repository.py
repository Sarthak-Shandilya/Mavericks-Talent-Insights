"""Repository layer for Training Coordinator queries."""
from __future__ import annotations

from datetime import datetime, timedelta, UTC

from sqlalchemy import func, select, and_, or_, case
from sqlalchemy.orm import Session, joinedload

from models.automation import PerformanceClassification
from models.trainee import Assessment, Batch, Trainee, TraineeStage
from models.upload_audit import UploadBatch, UploadRowError
from models.user import User


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def count_active_trainees(db: Session) -> int:
    return db.execute(
        select(func.count()).select_from(Trainee).where(
            Trainee.is_active == True,
            Trainee.training_status == "Active",
        )
    ).scalar_one()


def count_active_trainees_before(db: Session, days: int) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    return db.execute(
        select(func.count()).select_from(Trainee).where(
            Trainee.is_active == True,
            Trainee.training_status == "Active",
            Trainee.created_at < cutoff,
        )
    ).scalar_one()


def get_average_performance_score(db: Session) -> float:
    result = db.execute(
        select(func.avg(PerformanceClassification.composite_score)).where(
            PerformanceClassification.composite_score.isnot(None)
        )
    ).scalar_one()
    return float(result or 0.0)


def get_average_performance_score_before(db: Session, days: int) -> float:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    result = db.execute(
        select(func.avg(PerformanceClassification.composite_score)).where(
            PerformanceClassification.composite_score.isnot(None),
            PerformanceClassification.computed_at < cutoff,
        )
    ).scalar_one()
    return float(result or 0.0)


def count_total_assessments(db: Session) -> int:
    return db.execute(select(func.count()).select_from(Assessment)).scalar_one()


def count_upload_errors_recent(db: Session, days: int = 30) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    return db.execute(
        select(func.count()).select_from(UploadRowError).join(
            UploadBatch, UploadBatch.id == UploadRowError.upload_id
        ).where(UploadBatch.created_at >= cutoff)
    ).scalar_one()


# ---------------------------------------------------------------------------
# Recent uploads
# ---------------------------------------------------------------------------

def get_recent_uploads(db: Session, user_email: str | None, limit: int = 10) -> list[UploadBatch]:
    stmt = (
        select(UploadBatch)
        .options(joinedload(UploadBatch.uploaded_by))
        .order_by(UploadBatch.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().unique().all())


# ---------------------------------------------------------------------------
# Batch info (dashboard)
# ---------------------------------------------------------------------------

def get_all_batches_with_trainees(db: Session) -> list[Batch]:
    stmt = (
        select(Batch)
        .options(
            joinedload(Batch.trainees).joinedload(Trainee.performance_classification),
            joinedload(Batch.trainees).joinedload(Trainee.stream),
            joinedload(Batch.trainees).joinedload(Trainee.current_training_stage),
            joinedload(Batch.trainees).joinedload(Trainee.stage_rows).joinedload(TraineeStage.stage_type),
        )
        .order_by(Batch.created_at.desc())
    )
    return list(db.execute(stmt).scalars().unique().all())


# ---------------------------------------------------------------------------
# Trainee list
# ---------------------------------------------------------------------------

def fetch_trainees_filtered(
    db: Session,
    *,
    name: str | None,
    emp_id: str | None,
    batch_code: str | None,
    stream_code: str | None,
    status: str | None,
    limit: int,
    offset: int,
) -> tuple[int, list[Trainee]]:
    from models.reference import Stream
    from models.trainee import Batch

    stmt = (
        select(Trainee)
        .options(
            joinedload(Trainee.batch),
            joinedload(Trainee.stream),
            joinedload(Trainee.current_training_stage),
            joinedload(Trainee.performance_classification),
        )
        .where(Trainee.is_active == True)
    )

    if name:
        stmt = stmt.where(Trainee.full_name.ilike(f"%{name}%"))
    if emp_id:
        stmt = stmt.where(Trainee.employee_id.ilike(f"%{emp_id}%"))
    if batch_code and batch_code not in ("All Batches", "all"):
        stmt = stmt.join(Batch, Batch.id == Trainee.batch_id).where(Batch.code == batch_code)
    if stream_code and stream_code not in ("All Streams", "all"):
        stmt = stmt.join(Stream, Stream.id == Trainee.stream_id).where(Stream.code == stream_code)
    if status and status not in ("all", "All"):
        stmt = stmt.where(Trainee.training_status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    stmt = stmt.order_by(Trainee.updated_at.desc()).limit(limit).offset(offset)
    trainees = list(db.execute(stmt).scalars().unique().all())
    return total, trainees


# ---------------------------------------------------------------------------
# Batch screen
# ---------------------------------------------------------------------------

def get_upload_error_counts_by_batch(db: Session) -> dict[str, int]:
    """Return {batch_code: error_count} for all batches via upload type heuristic."""
    # We approximate by counting row errors across all uploads in last 90 days
    cutoff = datetime.now(UTC) - timedelta(days=90)
    rows = db.execute(
        select(
            UploadBatch.upload_type,
            func.sum(UploadBatch.error_count).label("errs"),
        )
        .where(UploadBatch.created_at >= cutoff)
        .group_by(UploadBatch.upload_type)
    ).all()
    # returns a flat count; batch-level attribution requires file naming conventions
    return {r[0]: int(r[1] or 0) for r in rows}


def get_all_uploads_for_user(db: Session, user_email: str) -> list[UploadBatch]:
    from models.user import User as UserModel
    user = db.execute(
        select(UserModel).where(UserModel.email == user_email)
    ).scalar_one_or_none()

    stmt = (
        select(UploadBatch)
        .options(joinedload(UploadBatch.uploaded_by))
        .order_by(UploadBatch.created_at.desc())
    )
    if user:
        stmt = stmt.where(UploadBatch.uploaded_by_user_id == user.id)

    return list(db.execute(stmt).scalars().unique().all())
