"""Business Head read-only APIs."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apis.deps import require_roles
from configs.constants import RoleName
from models.user import User
from schemas.stakeholder import (
    BusinessHeadDashboardResponse,
    StakeholderDashboardRequest,
    StreamTrendsResponse,
    TopperSummaryResponse,
)
from services import stakeholder_service
from utils.database import get_db

router = APIRouter(prefix="/business_head", tags=["business head"])


@router.post("/dashboard", response_model=BusinessHeadDashboardResponse)
def dashboard(
    body: StakeholderDashboardRequest,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(RoleName.BUSINESS_HEAD))],
) -> BusinessHeadDashboardResponse:
    return stakeholder_service.business_head_dashboard(db)


@router.post("/stream-trends", response_model=StreamTrendsResponse)
def stream_trends(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(RoleName.BUSINESS_HEAD))],
) -> StreamTrendsResponse:
    return stakeholder_service.business_head_stream_trends(db)


@router.post("/topper-summary", response_model=TopperSummaryResponse)
def topper_summary(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_roles(RoleName.BUSINESS_HEAD))],
) -> TopperSummaryResponse:
    return stakeholder_service.business_head_topper_summary(db)
