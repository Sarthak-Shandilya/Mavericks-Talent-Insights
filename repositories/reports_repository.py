"""Report query layer."""
from __future__ import annotations

from datetime import date, datetime, UTC

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.automation import PerformanceClassification, TopperFlag
from models.reference import TrainingStageType
from models.trainee import Assessment, Batch, Trainee, TraineeCompetency, TraineeStage
from schemas.reports import ReportFilters


def _trainee_filter_stmt(filters: ReportFilters):
    q = select(Trainee).options(
        joinedload(Trainee.batch),
        joinedload(Trainee.stream),
        joinedload(Trainee.current_training_stage),
        joinedload(Trainee.performance_classification),
    ).where(Trainee.is_active.is_(True))
    if filters.batch_code:
        q = q.join(Batch).where(Batch.code == filters.batch_code)
    if filters.stream:
        from models.reference import Stream
        q = q.join(Stream).where(Stream.code == filters.stream)
    if filters.location:
        q = q.where(
            (Trainee.base_location == filters.location)
            | (Trainee.current_training_location == filters.location)
        )
    if filters.employee_id:
        q = q.where(Trainee.employee_id == filters.employee_id)
    return q


def fetch_trainees_for_report(db: Session, filters: ReportFilters) -> list[Trainee]:
    return list(db.execute(_trainee_filter_stmt(filters)).unique().scalars().all())


def batch_performance_rows(db: Session, filters: ReportFilters) -> list[dict]:
    batches = db.execute(select(Batch).order_by(Batch.code)).scalars().all()
    rows = []
    for batch in batches:
        if filters.batch_code and batch.code != filters.batch_code:
            continue
        trainees = [t for t in batch.trainees if t.is_active]
        if filters.stream:
            trainees = [t for t in trainees if t.stream and t.stream.code == filters.stream]
        if not trainees:
            continue
        scores = [
            float(t.performance_classification.composite_score)
            for t in trainees
            if t.performance_classification and t.performance_classification.composite_score
        ]
        high = sum(1 for t in trainees if t.performance_classification and t.performance_classification.classification == "HIGH")
        avg = sum(1 for t in trainees if t.performance_classification and t.performance_classification.classification == "AVERAGE")
        low = sum(1 for t in trainees if t.performance_classification and t.performance_classification.classification == "LOW")
        completed = sum(1 for t in trainees if t.training_status in ("Completed", "COMPLETED"))
        rows.append({
            "batch_code": batch.code,
            "batch_name": batch.name,
            "total_trainees": len(trainees),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "high_count": high,
            "average_count": avg,
            "low_count": low,
            "completion_rate": round(completed / len(trainees) * 100, 2) if trainees else 0.0,
        })
    return rows


def trainee_performance_detail(db: Session, employee_id: str) -> Trainee | None:
    return db.execute(
        select(Trainee)
        .options(
            joinedload(Trainee.batch),
            joinedload(Trainee.stream),
            joinedload(Trainee.current_training_stage),
            joinedload(Trainee.performance_classification),
            joinedload(Trainee.assessments),
            joinedload(Trainee.stage_rows).joinedload(TraineeStage.stage_type),
            joinedload(Trainee.competencies),
            joinedload(Trainee.topper_flags),
        )
        .where(Trainee.employee_id == employee_id)
    ).unique().scalar_one_or_none()


def stage_progress_rows(db: Session, filters: ReportFilters) -> list[dict]:
    stage_types = db.execute(select(TrainingStageType).order_by(TrainingStageType.sort_order)).scalars().all()
    trainees = fetch_trainees_for_report(db, filters)
    trainee_ids = {t.id for t in trainees}
    rows = []
    for st in stage_types:
        if filters.stage_code and st.code != filters.stage_code:
            continue
        stages = db.execute(
            select(TraineeStage).where(
                TraineeStage.stage_type_id == st.id,
                TraineeStage.trainee_id.in_(trainee_ids) if trainee_ids else False,
            )
        ).scalars().all() if trainee_ids else []
        completed = sum(1 for s in stages if s.status == "COMPLETED")
        pending = sum(1 for s in stages if s.status == "PENDING")
        na = sum(1 for s in stages if s.status == "NOT_APPLICABLE")
        scores = [float(s.score) for s in stages if s.score is not None]
        rows.append({
            "stage_code": st.code,
            "stage_label": st.label,
            "completed": completed,
            "pending": pending,
            "not_applicable": na,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
        })
    return rows


def topper_rows(db: Session, filters: ReportFilters) -> list[dict]:
    q = (
        select(TopperFlag, Trainee)
        .join(Trainee, TopperFlag.trainee_id == Trainee.id)
        .options(
            joinedload(Trainee.performance_classification),
            joinedload(Trainee.stream),
            joinedload(Trainee.batch),
        )
    )
    if filters.batch_code:
        q = q.join(Batch).where(Batch.code == filters.batch_code)
    rows = db.execute(q).all()
    result = []
    for flag, trainee in rows:
        if filters.stream and trainee.stream and trainee.stream.code != filters.stream:
            continue
        pc = trainee.performance_classification
        result.append({
            "employee_id": trainee.employee_id,
            "full_name": trainee.full_name,
            "topper_type": flag.topper_type,
            "scope_value": flag.scope_value,
            "rank": flag.rank,
            "composite_score": float(pc.composite_score) if pc and pc.composite_score else None,
        })
    return sorted(result, key=lambda r: (r["topper_type"], r.get("rank") or 999))


def competency_readiness_rows(db: Session, filters: ReportFilters) -> list[dict]:
    trainees = fetch_trainees_for_report(db, filters)
    trainee_ids = {t.id for t in trainees}
    comps = db.execute(
        select(TraineeCompetency).where(
            TraineeCompetency.trainee_id.in_(trainee_ids) if trainee_ids else False
        )
    ).scalars().all() if trainee_ids else []
    by_name: dict[str, list[TraineeCompetency]] = {}
    for c in comps:
        by_name.setdefault(c.competency_name, []).append(c)
    rows = []
    for name, items in sorted(by_name.items()):
        rows.append({
            "competency_name": name,
            "total": len(items),
            "completed": sum(1 for i in items if i.status == "COMPLETED"),
            "in_progress": sum(1 for i in items if i.status == "IN_PROGRESS"),
            "ready_count": sum(1 for i in items if i.readiness_flag),
        })
    return rows


def assessment_trend_points(db: Session, filters: ReportFilters) -> list[dict]:
    q = (
        select(Assessment)
        .join(Trainee, Assessment.trainee_id == Trainee.id)
        .options(joinedload(Assessment.trainee))
        .where(Trainee.is_active.is_(True))
    )
    if filters.batch_code:
        q = q.join(Batch).where(Batch.code == filters.batch_code)
    if filters.employee_id:
        q = q.where(Trainee.employee_id == filters.employee_id)
    if filters.date_from:
        q = q.where(Assessment.assessment_date >= filters.date_from)
    if filters.date_to:
        q = q.where(Assessment.assessment_date <= filters.date_to)
    assessments = db.execute(q.limit(5000)).scalars().all()
    return [
        {
            "employee_id": a.trainee.employee_id,
            "assessment_code": a.assessment_code,
            "attempt_no": a.attempt_no,
            "score": float(a.score),
            "max_score": float(a.max_score),
            "assessment_date": a.assessment_date,
        }
        for a in assessments
    ]
