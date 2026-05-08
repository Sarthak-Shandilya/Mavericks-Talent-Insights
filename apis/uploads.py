from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from apis.deps import require_roles
from configs.constants import RoleName
from models.enums import UploadType
from models.user import User
from schemas.upload import UploadCreateResponse, UploadStatusResponse
from services import upload_service
from utils.database import get_db

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/{upload_type}", response_model=UploadCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_upload(
    upload_type: UploadType,
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    template_version: Annotated[str | None, Form()] = None,
    current_user: Annotated[
        User,
        Depends(require_roles(RoleName.SYSTEM_ADMIN, RoleName.TRAINING_COORDINATOR)),
    ] = None,
) -> UploadCreateResponse:
    row = upload_service.create_upload(
        db=db,
        upload_type=upload_type,
        template_version=template_version,
        current_user=current_user,
        file=file,
    )
    return UploadCreateResponse(
        upload_id=row.id,
        status=row.status,
        message="Upload accepted and queued for ingestion",
    )


@router.get("/{upload_id}", response_model=UploadStatusResponse)
def get_upload_status(
    upload_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[
        User,
        Depends(require_roles(RoleName.SYSTEM_ADMIN, RoleName.TRAINING_COORDINATOR, RoleName.TRAINER, RoleName.HR, RoleName.BUSINESS_HEAD)),
    ] = None,
) -> UploadStatusResponse:
    row = upload_service.get_upload(db, upload_id)
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    return UploadStatusResponse.model_validate(row)


@router.get("/templates/{upload_type}")
def download_template(
    upload_type: UploadType,
    _current_user: Annotated[
        User,
        Depends(require_roles(RoleName.SYSTEM_ADMIN, RoleName.TRAINING_COORDINATOR)),
    ] = None,
) -> Response:
    file_name, content = upload_service.build_template(upload_type)
    headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
