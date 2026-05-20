"""Training Coordinator API routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from apis.deps import require_roles
from configs.constants import RoleName
from models.enums import UploadType
from models.user import User
from schemas.training_coordinator import (
    BatchInfoRequest,
    BatchInfoResponse,
    BatchScreenRequest,
    BatchScreenResponse,
    DashboardRequest,
    DashboardResponse,
    DownloadTraineesRequest,
    FetchTraineesRequest,
    FetchTraineesResponse,
    PostUploadResponse,
    UploadInfoRequest,
    UploadInfoResponse,
)
from services import training_coordinator_service, upload_service
from utils.database import get_db

router = APIRouter(prefix="/training_coordinator", tags=["training coordinator"])

_TC_ROLES = (RoleName.TRAINING_COORDINATOR, RoleName.SYSTEM_ADMIN)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.post(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Training Coordinator dashboard KPIs",
)
def dashboard_fetch(
    body: DashboardRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(*_TC_ROLES))],
) -> DashboardResponse:
    return training_coordinator_service.get_dashboard(db, current_user.email)


# ---------------------------------------------------------------------------
# Upload info widget
# ---------------------------------------------------------------------------

@router.post(
    "/upload-info",
    response_model=UploadInfoResponse,
    summary="Recent uploads for the dashboard widget",
)
def upload_info_fetch(
    body: UploadInfoRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(*_TC_ROLES))],
) -> UploadInfoResponse:
    return training_coordinator_service.get_upload_info(db, current_user.email)


# ---------------------------------------------------------------------------
# Batch info widget (dashboard)
# ---------------------------------------------------------------------------

@router.post(
    "/batch-info",
    response_model=BatchInfoResponse,
    summary="Batch summary cards for the dashboard",
)
def batch_info_fetch(
    body: BatchInfoRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(*_TC_ROLES))],
) -> BatchInfoResponse:
    return training_coordinator_service.get_batch_info_dashboard(db, current_user.email)


# ---------------------------------------------------------------------------
# Trainees list
# ---------------------------------------------------------------------------

@router.post(
    "/trainees",
    response_model=FetchTraineesResponse,
    summary="Paginated and filtered trainee list",
)
def fetch_trainees(
    body: FetchTraineesRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(*_TC_ROLES))],
) -> FetchTraineesResponse:
    return training_coordinator_service.fetch_trainees(db, body, current_user.email)


# ---------------------------------------------------------------------------
# Download trainees as Excel
# ---------------------------------------------------------------------------

@router.post(
    "/trainees/download",
    summary="Export filtered trainee list to Excel (.xlsx)",
    response_class=Response,
)
def download_trainees(
    body: DownloadTraineesRequest,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(require_roles(*_TC_ROLES))],
) -> Response:
    file_name, content = training_coordinator_service.download_trainees_excel(db, body)
    headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Batches screen
# ---------------------------------------------------------------------------

@router.post(
    "/batches",
    response_model=BatchScreenResponse,
    summary="Full batch info screen with per-batch analytics",
)
def batch_screen_fetch(
    body: BatchScreenRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(*_TC_ROLES))],
) -> BatchScreenResponse:
    return training_coordinator_service.get_batch_screen(db, current_user.email)


# ---------------------------------------------------------------------------
# Ingestion screen — post upload (delegates to upload_service, returns history)
# ---------------------------------------------------------------------------

@router.post(
    "/ingestion/upload/{upload_type}",
    response_model=PostUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload Excel file and return updated upload history",
)
def post_upload(
    upload_type: UploadType,
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    template_version: Annotated[str | None, Form()] = None,
    current_user: Annotated[User, Depends(require_roles(*_TC_ROLES))] = None,
) -> PostUploadResponse:
    row = upload_service.create_upload(
        db=db,
        upload_type=upload_type,
        template_version=template_version,
        current_user=current_user,
        file=file,
    )
    history = training_coordinator_service.get_user_upload_history(db, current_user.email)
    return PostUploadResponse(upload_id=row.id, user_uploads=history)
