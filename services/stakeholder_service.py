"""Trainer, HR, and Business Head read-only dashboards."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.automation import PerformanceClassification, TopperFlag
from models.trainee import Batch, Trainee, TraineeCompetency
from models.reference import Stream
from schemas.stakeholder import (
    BusinessHeadDashboardResponse,
    DemographicsResponse,
    DemographicsRow,
    HRDashboardResponse,
    StreamTrendRow,
    StreamTrendsResponse,
    TopperSummaryResponse,
    TopperSummaryRow,
    TraineeSummaryItem,
    TrainerDashboardResponse,
)
import repositories.training_coordinator_repository as tc_repo


def trainer_dashboard(db: Session) -> TrainerDashboardResponse:
    active = tc_repo.count_active_trainees(db)
    avg = round(tc_repo.get_average_performance_score(db), 2)
    trainees = db.execute(
        select(Trainee).options(joinedload(Trainee.performance_classification)).where(Trainee.is_active.is_(True))
    ).unique().scalars().all()
    high = sum(1 for t in trainees if t.performance_classification and t.performance_classification.classification == "HIGH")
    low = sum(1 for t in trainees if t.performance_classification and t.performance_classification.classification == "LOW")
    return TrainerDashboardResponse(total_trainees=active, high_performers=high, low_performers=low, avg_score=avg)


def trainer_trainees(db: Session, limit: int = 50, offset: int = 0) -> list[TraineeSummaryItem]:
    rows = db.execute(
        select(Trainee)
        .options(
            joinedload(Trainee.batch),
            joinedload(Trainee.stream),
            joinedload(Trainee.current_training_stage),
            joinedload(Trainee.performance_classification),
        )
        .where(Trainee.is_active.is_(True))
        .limit(limit)
        .offset(offset)
    ).unique().scalars().all()
    return [
        TraineeSummaryItem(
            employee_id=t.employee_id,
            full_name=t.full_name,
            batch=t.batch.code if t.batch else None,
            stream=t.stream.code if t.stream else None,
            performance=t.performance_classification.classification if t.performance_classification else None,
            current_stage=t.current_training_stage.code if t.current_training_stage else None,
        )
        for t in rows
    ]


def hr_dashboard(db: Session) -> HRDashboardResponse:
    active = tc_repo.count_active_trainees(db)
    all_t = db.execute(select(func.count()).select_from(Trainee)).scalar_one()
    completed = db.execute(
        select(func.count()).select_from(Trainee).where(Trainee.training_status.in_(("Completed", "COMPLETED")))
    ).scalar_one()
    ready = db.execute(
        select(func.count()).select_from(TraineeCompetency).where(TraineeCompetency.readiness_flag.is_(True))
    ).scalar_one()
    avg = round(tc_repo.get_average_performance_score(db), 2)
    rate = round(completed / all_t * 100, 2) if all_t else 0.0
    return HRDashboardResponse(
        total_active=active,
        completion_rate=rate,
        competency_ready_count=ready,
        avg_performance=avg,
    )


def hr_demographics(db: Session) -> DemographicsResponse:
    rows = []
    for field, col in [
        ("base_location", Trainee.base_location),
        ("college_state", Trainee.college_state),
        ("batch", Batch.code),
    ]:
        if field == "batch":
            data = db.execute(
                select(Batch.code, func.count(Trainee.id))
                .join(Trainee, Trainee.batch_id == Batch.id)
                .group_by(Batch.code)
            ).all()
        else:
            data = db.execute(select(col, func.count()).group_by(col)).all()
        for value, count in data:
            rows.append(DemographicsRow(dimension=field, value=str(value), count=count))
    return DemographicsResponse(rows=rows)


def business_head_dashboard(db: Session) -> BusinessHeadDashboardResponse:
    batches = db.execute(select(func.count()).select_from(Batch)).scalar_one()
    trainees = tc_repo.count_active_trainees(db)
    avg = round(tc_repo.get_average_performance_score(db), 2)
    toppers = db.execute(select(func.count()).select_from(TopperFlag)).scalar_one()
    return BusinessHeadDashboardResponse(
        total_batches=batches,
        total_trainees=trainees,
        overall_avg_score=avg,
        topper_count=toppers,
    )


def business_head_stream_trends(db: Session) -> StreamTrendsResponse:
    streams = db.execute(select(Stream)).scalars().all()
    rows = []
    for s in streams:
        trainees = db.execute(
            select(Trainee)
            .options(joinedload(Trainee.performance_classification))
            .where(Trainee.stream_id == s.id, Trainee.is_active.is_(True))
        ).unique().scalars().all()
        scores = [
            float(t.performance_classification.composite_score)
            for t in trainees
            if t.performance_classification and t.performance_classification.composite_score
        ]
        rows.append(
            StreamTrendRow(
                stream=s.code,
                trainee_count=len(trainees),
                avg_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
            )
        )
    return StreamTrendsResponse(rows=rows)


def business_head_topper_summary(db: Session) -> TopperSummaryResponse:
    data = db.execute(
        select(TopperFlag.topper_type, func.count()).group_by(TopperFlag.topper_type)
    ).all()
    return TopperSummaryResponse(rows=[TopperSummaryRow(topper_type=t, count=c) for t, c in data])
