"""Pydantic schemas for Training Coordinator APIs."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardRequest(BaseModel):
    pass


class DashboardResponse(BaseModel):
    total_active_trainees: int
    increased_number_in_a_month: int
    average_performance_score: float
    increase_in_avg_score: float
    no_of_assessments: int
    no_of_upload_errors: int


# ---------------------------------------------------------------------------
# Upload info
# ---------------------------------------------------------------------------

class UploadInfoRequest(BaseModel):
    pass


class RecentUploadItem(BaseModel):
    upload_id: uuid.UUID
    name: str
    no_of_rows: int | None
    upload_type: str
    upload_status: str
    uploaded_at: datetime
    uploaded_by: str


class UploadInfoResponse(BaseModel):
    recent_uploads: list[RecentUploadItem]


# ---------------------------------------------------------------------------
# Batch info (dashboard widget)
# ---------------------------------------------------------------------------

class BatchInfoRequest(BaseModel):
    pass


class ScoreConsolidation(BaseModel):
    high: int
    medium: int
    low: int


class DashboardBatchItem(BaseModel):
    batch_code: str
    start_date: date | None
    stream: str | None
    total_candidates: int
    avg_score: float
    score_consolidation: ScoreConsolidation
    avg_completion: float
    status: str


class BatchInfoResponse(BaseModel):
    data: list[DashboardBatchItem]


# ---------------------------------------------------------------------------
# Trainee list
# ---------------------------------------------------------------------------

class SearchBy(BaseModel):
    name: str | None = None
    id: str | None = None


class TraineeFilters(BaseModel):
    search_by: SearchBy = SearchBy()
    batch: str | None = None          # "All Batches" or batch_code
    stream: str | None = None         # "All Streams" or stream code
    status: str | None = None         # Active / On Hold / Completed / Dropped


class Pagination(BaseModel):
    limit: int = 50
    offset: int = 0


class FetchTraineesRequest(BaseModel):
    filters: TraineeFilters = TraineeFilters()
    pagination: Pagination = Pagination()


class ActionsAvailable(BaseModel):
    export_to_excel: bool = True
    add_trainee: bool = True
    clear_filters: bool = True


class ResponseMetadata(BaseModel):
    total_results: int
    filters_applied: TraineeFilters
    actions_available: ActionsAvailable


class TraineeListItem(BaseModel):
    emp_id: str
    trainee_name: str
    batch: str | None
    stream: str | None
    current_stage: str | None
    performance: str | None          # HIGH / AVERAGE / LOW
    last_updated: datetime | None


class FetchTraineesResponse(BaseModel):
    metadata: ResponseMetadata
    data: list[TraineeListItem]


# ---------------------------------------------------------------------------
# Download trainees Excel
# ---------------------------------------------------------------------------

class DownloadTraineesRequest(BaseModel):
    batch_code: str | None = None
    stream: str | None = None
    current_stage: str | None = None


# ---------------------------------------------------------------------------
# Batches info screen
# ---------------------------------------------------------------------------

class BatchScreenRequest(BaseModel):
    pass


class BatchWiseInfo(BaseModel):
    batch_code: str
    from_date: date | None
    due_date: date | None
    trainer_name: str | None
    no_of_trainees: int
    avg_score: float
    completion_percentage: float
    current_stage: str | None
    high_performers: int
    medium_performers: int
    low_performers: int
    stream: str | None
    upload_error_count: int


class BatchScreenResponse(BaseModel):
    total_batches: int
    total_trainees: int
    overall_avg: float
    completion_rate: float
    batch_wise_info: list[BatchWiseInfo]


# ---------------------------------------------------------------------------
# Upload (Ingestion screen)
# ---------------------------------------------------------------------------

class UploadHistoryItem(BaseModel):
    file_id: uuid.UUID
    datetime: datetime
    file_name: str
    type: str
    status: str
    rows: int | None
    uploaded_by: str
    error_count: int | None


class PostUploadResponse(BaseModel):
    upload_id: uuid.UUID
    user_uploads: list[UploadHistoryItem]
