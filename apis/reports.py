"""Structured reporting APIs (BRD §7.8)."""
from __future__ import annotations

from typing import Annotated, Union

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from apis.deps import require_roles
from configs.constants import RoleName
from models.user import User
from schemas.reports import (
    AssessmentTrendReport,
    BatchPerformanceReport,
    CompetencyReadinessReport,
    ReportFilters,
    StageProgressReport,
    TopperReport,
    TraineePerformanceReport,
)
from services import reports_service
from utils.database import get_db

router = APIRouter(prefix="/reports", tags=["reports"])

_REPORT_ROLES = (
    RoleName.TRAINING_COORDINATOR,
    RoleName.SYSTEM_ADMIN,
    RoleName.TRAINER,
    RoleName.HR,
    RoleName.BUSINESS_HEAD,
)


@router.post("/batch-performance", response_model=None)
def post_batch_performance(
    body: ReportFilters,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(*_REPORT_ROLES))],
) -> Union[BatchPerformanceReport, Response]:
    return reports_service.batch_performance(db, body)


@router.post("/trainee-performance", response_model=None)
def post_trainee_performance(
    body: ReportFilters,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(*_REPORT_ROLES))],
) -> Union[TraineePerformanceReport, Response]:
    return reports_service.trainee_performance(db, body)


@router.post("/stage-progress", response_model=None)
def post_stage_progress(
    body: ReportFilters,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(*_REPORT_ROLES))],
) -> Union[StageProgressReport, Response]:
    return reports_service.stage_progress(db, body)


@router.post("/toppers", response_model=None)
def post_toppers(
    body: ReportFilters,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(*_REPORT_ROLES))],
) -> Union[TopperReport, Response]:
    return reports_service.toppers(db, body)


@router.post("/competency-readiness", response_model=None)
def post_competency_readiness(
    body: ReportFilters,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(*_REPORT_ROLES))],
) -> Union[CompetencyReadinessReport, Response]:
    return reports_service.competency_readiness(db, body)


@router.post("/assessment-trends", response_model=None)
def post_assessment_trends(
    body: ReportFilters,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(*_REPORT_ROLES))],
) -> Union[AssessmentTrendReport, Response]:
    return reports_service.assessment_trends(db, body)
