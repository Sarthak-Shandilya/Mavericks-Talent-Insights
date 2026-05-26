"""HR read-only APIs."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apis.deps import require_roles
from configs.constants import RoleName
from models.user import User
from schemas.stakeholder import (
    DemographicsResponse,
    HRDashboardResponse,
    StakeholderDashboardRequest,
)
from services import stakeholder_service
from utils.database import get_db

router = APIRouter(prefix="/hr", tags=["hr"])


@router.post("/dashboard", response_model=HRDashboardResponse)
def dashboard(
    body: StakeholderDashboardRequest,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(RoleName.HR))],
) -> HRDashboardResponse:
    return stakeholder_service.hr_dashboard(db)


@router.post("/demographics", response_model=DemographicsResponse)
def demographics(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(RoleName.HR))],
) -> DemographicsResponse:
    return stakeholder_service.hr_demographics(db)


@router.post("/competency-summary", response_model=DemographicsResponse)
def competency_summary(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(RoleName.HR))],
) -> DemographicsResponse:
    from schemas.reports import ReportFilters
    from services import reports_service

    report = reports_service.competency_readiness(db, ReportFilters(format="json"))
    rows = [
        {"dimension": "competency", "value": r.competency_name, "count": r.total}
        for r in report.rows
    ]
    from schemas.stakeholder import DemographicsRow
    return DemographicsResponse(rows=[DemographicsRow(**row) for row in rows])
