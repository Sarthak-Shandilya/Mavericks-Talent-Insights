from __future__ import annotations

import uuid
from datetime import UTC, datetime
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from configs.settings import get_settings
from configs.upload_template_headers import (
    ASSESSMENTS_HEADERS,
    COMPETENCY_HEADERS,
    STAGES_HEADERS,
    TRAINEE_MASTER_HEADERS,
)
from models.enums import UploadStatus, UploadType
from models.upload_audit import UploadBatch
from models.user import User
from schemas.upload import UploadStatusResponse
from storage import get_storage_client
from utils.hashing import sha256_hex
from utils.queue_clients import get_queue_client

_ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}


def _validate_file(file_name: str, content_type: str | None, size_bytes: int) -> None:
    settings = get_settings()
    if not file_name.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are supported",
        )
    if content_type and content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file content type",
        )
    max_size_bytes = settings.upload_max_file_size_mb * 1024 * 1024
    if size_bytes > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.upload_max_file_size_mb} MB",
        )


def create_upload(
    *,
    db: Session,
    upload_type: UploadType,
    template_version: str | None,
    current_user: User,
    file: UploadFile,
) -> UploadBatch:
    payload = file.file.read()
    file.file.seek(0)
    _validate_file(file.filename or "upload.xlsx", file.content_type, len(payload))

    file_hash = sha256_hex(payload)
    duplicate_stmt = (
        select(UploadBatch)
        .where(UploadBatch.file_hash == file_hash)
        .where(UploadBatch.status.in_([UploadStatus.QUEUED.value, UploadStatus.PROCESSING.value, UploadStatus.COMPLETED.value]))
        .order_by(UploadBatch.created_at.desc())
    )
    existing = db.execute(duplicate_stmt).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"File already uploaded (upload_id={existing.id})",
        )

    upload_id = uuid.uuid4()
    file_name = file.filename or f"{upload_type.value.lower()}.xlsx"
    key = f"{upload_type.value}/{upload_id}/{file_name}"
    blob_url = get_storage_client().save_bytes(
        key=key,
        data=payload,
        content_type=file.content_type,
    )

    row = UploadBatch(
        id=upload_id,
        upload_type=upload_type.value,
        file_name=file_name,
        blob_url=blob_url,
        file_hash=file_hash,
        status=UploadStatus.QUEUED.value,
        template_version=template_version,
        uploaded_by_user_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    from services import audit_service

    audit_service.log_action(
        db,
        actor=current_user,
        action="upload.create",
        entity_type="upload_batch",
        entity_id=row.id,
        details={"upload_type": upload_type.value, "file_name": file_name},
    )
    db.commit()

    now = datetime.now(UTC).isoformat()
    message = {
        "message_id": str(uuid.uuid4()),
        "upload_id": str(row.id),
        "upload_type": row.upload_type,
        "file_url": row.blob_url,
        "file_hash": row.file_hash,
        "template_version": row.template_version or "v1",
        "requested_by_user_id": str(current_user.id),
        "requested_at": now,
    }
    settings = get_settings()
    try:
        get_queue_client().publish(
            queue_name=settings.queue_name_ingestion,
            message=message,
            message_id=message["message_id"],
        )
    except Exception as exc:
        row.status = UploadStatus.FAILED.value
        row.percentage_completed = 0
        row.completed_at = datetime.now(UTC)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Upload saved but queue publish failed (upload_id={row.id}). "
                "Batch marked FAILED; check ActiveMQ/Service Bus and QUEUE_TYPE settings."
            ),
        ) from exc
    return row


def resolve_percentage_completed(row: UploadBatch) -> int:
    """Return 0–100 for status API; uses persisted value or status-based fallback."""
    if row.percentage_completed is not None:
        pct = int(row.percentage_completed)
        if row.status == UploadStatus.FAILED.value:
            return min(99, pct)
        return min(100, max(0, pct))

    if row.status == UploadStatus.COMPLETED.value:
        return 100
    if row.status == UploadStatus.QUEUED.value:
        return 0
    if row.status == UploadStatus.FAILED.value:
        if row.row_count and row.row_count > 0:
            processed = (row.success_count or 0) + (row.error_count or 0)
            return min(99, int(processed / row.row_count * 100))
        return 0
    if row.status == UploadStatus.PROCESSING.value:
        if row.row_count and row.row_count > 0:
            processed = (row.success_count or 0) + (row.error_count or 0)
            return min(99, int(processed / row.row_count * 100))
        return 0
    return 0


def build_upload_status_response(row: UploadBatch) -> UploadStatusResponse:
    base = UploadStatusResponse.model_validate(row)
    return base.model_copy(update={"percentage_completed": resolve_percentage_completed(row)})


def get_upload(db: Session, upload_id: uuid.UUID) -> UploadBatch | None:
    stmt = select(UploadBatch).where(UploadBatch.id == upload_id)
    return db.execute(stmt).scalars().first()


def build_template(upload_type: UploadType) -> tuple[str, bytes]:
    headers_by_type = {
        UploadType.TRAINEE_MASTER: list(TRAINEE_MASTER_HEADERS),
        UploadType.ASSESSMENTS: list(ASSESSMENTS_HEADERS),
        UploadType.STAGES: list(STAGES_HEADERS),
        UploadType.COMPETENCY: list(COMPETENCY_HEADERS),
    }
    workbook = Workbook()
    sheet = workbook.active
    headers = headers_by_type[upload_type]
    for col, header in enumerate(headers, start=1):
        sheet.cell(row=1, column=col).value = header
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return f"{upload_type.value.lower()}_template.xlsx", stream.read()
