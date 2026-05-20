"""Business logic for Training Coordinator APIs."""
from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from sqlalchemy.orm import Session

import repositories.training_coordinator_repository as repo
from models.trainee import Batch, Trainee
from schemas.training_coordinator import (
    BatchInfoResponse,
    BatchScreenResponse,
    BatchWiseInfo,
    DashboardBatchItem,
    DashboardResponse,
    DownloadTraineesRequest,
    FetchTraineesRequest,
    FetchTraineesResponse,
    PostUploadResponse,
    RecentUploadItem,
    ResponseMetadata,
    ScoreConsolidation,
    TraineeFilters,
    TraineeListItem,
    UploadHistoryItem,
    UploadInfoResponse,
)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def get_dashboard(db: Session, user_email: str) -> DashboardResponse:
    current_active = repo.count_active_trainees(db)
    prev_active = repo.count_active_trainees_before(db, days=30)
    increased = current_active - prev_active

    current_avg = round(repo.get_average_performance_score(db), 2)
    prev_avg = round(repo.get_average_performance_score_before(db, days=30), 2)
    avg_increase = round(current_avg - prev_avg, 2)

    assessment_count = repo.count_total_assessments(db)
    upload_errors = repo.count_upload_errors_recent(db, days=30)

    return DashboardResponse(
        total_active_trainees=current_active,
        increased_number_in_a_month=increased,
        average_performance_score=current_avg,
        increase_in_avg_score=avg_increase,
        no_of_assessments=assessment_count,
        no_of_upload_errors=upload_errors,
    )


# ---------------------------------------------------------------------------
# Upload info
# ---------------------------------------------------------------------------

def get_upload_info(db: Session, user_email: str) -> UploadInfoResponse:
    uploads = repo.get_recent_uploads(db, user_email, limit=10)

    items = [
        RecentUploadItem(
            upload_id=u.id,
            name=u.file_name,
            no_of_rows=u.row_count,
            upload_type=u.upload_type,
            upload_status=u.status,
            uploaded_at=u.created_at,
            uploaded_by=u.uploaded_by.full_name or u.uploaded_by.email if u.uploaded_by else "Unknown",
        )
        for u in uploads
    ]
    return UploadInfoResponse(recent_uploads=items)


# ---------------------------------------------------------------------------
# Batch info (dashboard widget)
# ---------------------------------------------------------------------------

def _classify_batch_status(batch: Batch) -> str:
    active_trainees = [t for t in batch.trainees if t.training_status == "Active" and t.is_active]
    completed = [t for t in batch.trainees if t.training_status == "Completed"]
    if not batch.trainees:
        return "Empty"
    completion_rate = len(completed) / len(batch.trainees) * 100
    if completion_rate >= 90:
        return "Completed"
    if active_trainees:
        return "Active"
    return "On Hold"


def _get_batch_performance_counts(trainees: list[Trainee]) -> ScoreConsolidation:
    high = sum(
        1 for t in trainees
        if t.performance_classification
        and t.performance_classification.classification == "HIGH"
    )
    low = sum(
        1 for t in trainees
        if t.performance_classification
        and t.performance_classification.classification == "LOW"
    )
    medium = len(trainees) - high - low
    return ScoreConsolidation(high=high, medium=medium, low=low)


def _get_batch_avg_score(trainees: list[Trainee]) -> float:
    scores = [
        float(t.performance_classification.composite_score)
        for t in trainees
        if t.performance_classification and t.performance_classification.composite_score is not None
    ]
    return round(sum(scores) / len(scores), 2) if scores else 0.0


def _get_batch_avg_completion(trainees: list[Trainee]) -> float:
    """Average % of stages marked completed per trainee."""
    if not trainees:
        return 0.0
    completion_rates = []
    for trainee in trainees:
        total_stages = len(trainee.stage_rows)
        if total_stages == 0:
            completion_rates.append(0.0)
            continue
        completed = sum(1 for s in trainee.stage_rows if s.status == "Completed")
        completion_rates.append(completed / total_stages * 100)
    return round(sum(completion_rates) / len(completion_rates), 2)


def get_batch_info_dashboard(db: Session, user_email: str) -> BatchInfoResponse:
    batches = repo.get_all_batches_with_trainees(db)
    items: list[DashboardBatchItem] = []

    for batch in batches:
        active_trainees = [t for t in batch.trainees if t.is_active]
        stream_label = (
            active_trainees[0].stream.label
            if active_trainees and active_trainees[0].stream
            else batch.stream_hint
        )
        items.append(
            DashboardBatchItem(
                batch_code=batch.code,
                start_date=batch.start_date,
                stream=stream_label,
                total_candidates=len(active_trainees),
                avg_score=_get_batch_avg_score(active_trainees),
                score_consolidation=_get_batch_performance_counts(active_trainees),
                avg_completion=_get_batch_avg_completion(active_trainees),
                status=_classify_batch_status(batch),
            )
        )

    return BatchInfoResponse(data=items)


# ---------------------------------------------------------------------------
# Trainees list
# ---------------------------------------------------------------------------

def fetch_trainees(db: Session, request: FetchTraineesRequest, user_email: str) -> FetchTraineesResponse:
    f = request.filters
    total, trainees = repo.fetch_trainees_filtered(
        db,
        name=f.search_by.name,
        emp_id=f.search_by.id,
        batch_code=f.batch,
        stream_code=f.stream,
        status=f.status,
        limit=request.pagination.limit,
        offset=request.pagination.offset,
    )

    items = []
    for t in trainees:
        perf = None
        if t.performance_classification:
            perf = t.performance_classification.classification

        items.append(
            TraineeListItem(
                emp_id=t.employee_id,
                trainee_name=t.full_name,
                batch=t.batch.code if t.batch else None,
                stream=t.stream.label if t.stream else None,
                current_stage=t.current_training_stage.label if t.current_training_stage else None,
                performance=perf,
                last_updated=t.updated_at,
            )
        )

    return FetchTraineesResponse(
        metadata=ResponseMetadata(
            total_results=total,
            filters_applied=f,
            actions_available=_build_actions(),
        ),
        data=items,
    )


def _build_actions():
    from schemas.training_coordinator import ActionsAvailable
    return ActionsAvailable(export_to_excel=True, add_trainee=True, clear_filters=True)


# ---------------------------------------------------------------------------
# Download trainees Excel
# ---------------------------------------------------------------------------

def download_trainees_excel(db: Session, req: DownloadTraineesRequest) -> tuple[str, bytes]:
    _, trainees = repo.fetch_trainees_filtered(
        db,
        name=None,
        emp_id=None,
        batch_code=req.batch_code,
        stream_code=req.stream,
        status=None,
        limit=10_000,
        offset=0,
    )
    if req.current_stage:
        trainees = [
            t for t in trainees
            if t.current_training_stage
            and t.current_training_stage.code == req.current_stage
        ]

    wb = Workbook()
    ws = wb.active
    ws.title = "Trainees"
    headers = [
        "Employee ID", "Full Name", "Gender", "Email", "Phone",
        "College Name", "College City", "College State",
        "Base Location", "Current Training Location", "Training Status",
        "Stream", "Current Stage", "Category", "Assigned Competency",
        "Batch", "Date of Joining", "Performance",
    ]
    ws.append(headers)

    for t in trainees:
        ws.append([
            t.employee_id,
            t.full_name,
            t.gender,
            t.email,
            t.phone,
            t.college_name,
            t.college_city,
            t.college_state,
            t.base_location,
            t.current_training_location,
            t.training_status,
            t.stream.label if t.stream else "",
            t.current_training_stage.label if t.current_training_stage else "",
            t.category,
            t.assigned_competency,
            t.batch.code if t.batch else "",
            str(t.doj),
            t.performance_classification.classification if t.performance_classification else "",
        ])

    buf = BytesIO()
    wb.save(buf)
    file_name = "trainees_export.xlsx"
    return file_name, buf.getvalue()


# ---------------------------------------------------------------------------
# Batch info screen
# ---------------------------------------------------------------------------

def get_batch_screen(db: Session, user_email: str) -> BatchScreenResponse:
    batches = repo.get_all_batches_with_trainees(db)

    all_trainees = [t for b in batches for t in b.trainees if t.is_active]
    total_trainees = len(all_trainees)
    all_scores = [
        float(t.performance_classification.composite_score)
        for t in all_trainees
        if t.performance_classification and t.performance_classification.composite_score is not None
    ]
    overall_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    all_stage_completions = []
    for t in all_trainees:
        total_stages = len(t.stage_rows)
        if total_stages > 0:
            completed = sum(1 for s in t.stage_rows if s.status == "Completed")
            all_stage_completions.append(completed / total_stages * 100)
    completion_rate = round(sum(all_stage_completions) / len(all_stage_completions), 2) if all_stage_completions else 0.0

    batch_wise: list[BatchWiseInfo] = []
    for batch in batches:
        active = [t for t in batch.trainees if t.is_active]
        avg_score = _get_batch_avg_score(active)
        perf = _get_batch_performance_counts(active)
        avg_comp = _get_batch_avg_completion(active)

        # Determine dominant current stage across batch
        stage_codes = [
            t.current_training_stage.label
            for t in active
            if t.current_training_stage
        ]
        dominant_stage = max(set(stage_codes), key=stage_codes.count) if stage_codes else None

        # Stream from first trainee
        stream_label = None
        if active and active[0].stream:
            stream_label = active[0].stream.label
        elif batch.stream_hint:
            stream_label = batch.stream_hint

        batch_wise.append(
            BatchWiseInfo(
                batch_code=batch.code,
                from_date=batch.start_date,
                due_date=None,           # not in model; extend if needed
                trainer_name=None,       # not in model; extend if needed
                no_of_trainees=len(active),
                avg_score=avg_score,
                completion_percentage=avg_comp,
                current_stage=dominant_stage,
                high_performers=perf.high,
                medium_performers=perf.medium,
                low_performers=perf.low,
                stream=stream_label,
                upload_error_count=0,    # batch-level attribution not stored; extend if needed
            )
        )

    return BatchScreenResponse(
        total_batches=len(batches),
        total_trainees=total_trainees,
        overall_avg=overall_avg,
        completion_rate=completion_rate,
        batch_wise_info=batch_wise,
    )


# ---------------------------------------------------------------------------
# Upload history for a user
# ---------------------------------------------------------------------------

def get_user_upload_history(db: Session, user_email: str) -> list[UploadHistoryItem]:
    uploads = repo.get_all_uploads_for_user(db, user_email)
    return [
        UploadHistoryItem(
            file_id=u.id,
            datetime=u.created_at,
            file_name=u.file_name,
            type=u.upload_type,
            status=u.status,
            rows=u.row_count,
            uploaded_by=u.uploaded_by.full_name or u.uploaded_by.email if u.uploaded_by else "Unknown",
            error_count=u.error_count,
        )
        for u in uploads
    ]
