import uuid
from datetime import datetime

from pydantic import BaseModel

from models.enums import UploadStatus, UploadType


class UploadCreateResponse(BaseModel):
    upload_id: uuid.UUID
    status: UploadStatus
    message: str


class UploadStatusResponse(BaseModel):
    id: uuid.UUID
    upload_type: UploadType
    file_name: str
    blob_url: str
    file_hash: str | None
    status: UploadStatus
    row_count: int | None
    success_count: int | None
    error_count: int | None
    template_version: str | None
    error_report_url: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
