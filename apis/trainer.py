"""Trainer read-only APIs."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apis.deps import require_roles
from configs.constants import RoleName
from models.user import User
from schemas.stakeholder import StakeholderDashboardRequest, TraineeSummaryItem, TrainerDashboardResponse
from services import stakeholder_service
from utils.database import get_db

router = APIRouter(prefix="/trainer", tags=["trainer"])


@router.post("/dashboard", response_model=TrainerDashboardResponse)
def dashboard(
    body: StakeholderDashboardRequest,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(RoleName.TRAINER))],
) -> TrainerDashboardResponse:
    return stakeholder_service.trainer_dashboard(db)


@router.post("/trainees", response_model=list[TraineeSummaryItem])
def trainees(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(RoleName.TRAINER))],
    limit: int = 50,
    offset: int = 0,
) -> list[TraineeSummaryItem]:
    return stakeholder_service.trainer_trainees(db, limit=limit, offset=offset)
