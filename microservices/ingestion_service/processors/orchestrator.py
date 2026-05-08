from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy import text

from configs.settings import get_settings
from db.session import SessionLocal
from parsers.excel_reader import iter_rows
from processors import upserter
from storage import get_storage_client
from utils.queue_clients import get_queue_client
from validators.row_schemas import AssessmentRow, CompetencyRow, StageRow, TraineeMasterRow

REQUIRED_TRAINEE_FIELDS = {
    "employee_id": ("employee_id", "employeeid"),
    "superset_id": ("superset_id", "supersetid"),
    "doj": ("doj", "date_of_joining"),
    "full_name": ("full_name", "name", "trainee_name"),
    "gender": ("gender",),
    "email": ("email", "email_id"),
    "phone": ("phone", "phone_number"),
    "college_name": ("college_name",),
    "college_city": ("college_city", "college_location_city"),
    "college_state": ("college_state", "college_location_state"),
    "base_location": ("base_location",),
    "current_training_location": ("current_training_location", "training_location"),
    "training_status": ("training_status",),
    "stream_code": ("stream", "stream_code"),
    "current_training_stage_code": ("current_training_stage", "stage", "stage_code"),
    "category": ("category",),
    "assigned_competency": ("assigned_competency", "competency"),
    "batch_code": ("batch_code", "batch"),
}

REQUIRED_ASSESSMENT_FIELDS = {
    "employee_id": ("employee_id",),
    "program": ("program",),
    "assessment_code": ("assessment_code", "code"),
    "attempt_no": ("attempt_no", "attempt"),
    "score": ("score",),
    "max_score": ("max_score",),
    "assessment_date": ("assessment_date", "date"),
    "remarks": ("remarks",),
}

REQUIRED_STAGE_FIELDS = {
    "employee_id": ("employee_id",),
    "stage_code": ("stage_code", "stage", "current_training_stage"),
    "status": ("status",),
    "score": ("score",),
    "attempts": ("attempts",),
    "completion_date": ("completion_date",),
}

REQUIRED_COMPETENCY_FIELDS = {
    "employee_id": ("employee_id",),
    "competency_name": ("competency_name", "assigned_competency"),
    "status": ("status",),
    "skill_level": ("skill_level",),
    "readiness_flag": ("readiness_flag",),
    "completion_date": ("completion_date",),
}


def _pick(row: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        if key in row:
            return row[key]
    return None


def _project_row(raw: dict[str, Any], field_map: dict[str, tuple[str, ...]]) -> dict[str, Any]:
    return {field: _pick(raw, aliases) for field, aliases in field_map.items()}


def _fetch_map(db, query: str) -> dict[str, Any]:
    rows = db.execute(text(query)).all()
    return {str(row[0]).upper(): row[1] for row in rows}


def _fetch_trainee_id_map(db) -> dict[str, Any]:
    rows = db.execute(text("SELECT employee_id, id FROM trainees")).all()
    return {str(row[0]).upper(): row[1] for row in rows}


def _insert_errors(db, upload_id: uuid.UUID, errors: list[dict]) -> None:
    if not errors:
        return
    stmt = text(
        """
        INSERT INTO upload_row_errors (id, upload_id, row_number, column_name, message, raw_payload)
        VALUES (:id, :upload_id, :row_number, :column_name, :message, :raw_payload)
        """
    )
    payload = []
    for err in errors:
        payload.append(
            {
                "id": uuid.uuid4(),
                "upload_id": upload_id,
                "row_number": err["row_number"],
                "column_name": err.get("column_name"),
                "message": err["message"],
                "raw_payload": err.get("raw_payload"),
            }
        )
    db.execute(stmt, payload)


def _mark_status(db, upload_id: uuid.UUID, status: str, **fields: Any) -> None:
    parts = ["status = :status"]
    params = {"upload_id": upload_id, "status": status}
    for key, value in fields.items():
        parts.append(f"{key} = :{key}")
        params[key] = value
    if status in ("COMPLETED", "FAILED"):
        parts.append("completed_at = :completed_at")
        params["completed_at"] = datetime.now(UTC)
    stmt = text(f"UPDATE upload_batches SET {', '.join(parts)} WHERE id = :upload_id")
    db.execute(stmt, params)


def _process_batch(
    *,
    db,
    upload_type: str,
    processed: list[dict],
) -> None:
    if not processed:
        return
    if upload_type == "TRAINEE_MASTER":
        upserter.upsert_trainees(db, processed)
    elif upload_type == "ASSESSMENTS":
        upserter.upsert_assessments(db, processed)
    elif upload_type == "STAGES":
        upserter.upsert_stages(db, processed)
    elif upload_type == "COMPETENCY":
        upserter.upsert_competencies(db, processed)
    else:
        raise ValueError(f"Unsupported upload_type: {upload_type}")


def process_upload(message: dict[str, Any]) -> None:
    upload_id = uuid.UUID(message["upload_id"])
    upload_type = str(message["upload_type"]).upper()
    batch_size = get_settings().ingestion_batch_size
    storage = get_storage_client()

    db = SessionLocal()
    try:
        _mark_status(db, upload_id, "PROCESSING")
        db.commit()

        payload = storage.read_bytes(url=message["file_url"])
        trainee_ids = _fetch_trainee_id_map(db)
        stream_ids = _fetch_map(db, "SELECT code, id FROM streams")
        stage_ids = _fetch_map(db, "SELECT code, id FROM training_stage_types")
        batch_ids = _fetch_map(db, "SELECT code, id FROM batches")

        pending: list[dict] = []
        errors: list[dict] = []
        success_count = 0
        row_count = 0

        for row_number, row in iter_rows(payload):
            row_count += 1
            try:
                if upload_type == "TRAINEE_MASTER":
                    projected = _project_row(row, REQUIRED_TRAINEE_FIELDS)
                    parsed = TraineeMasterRow.model_validate(projected)
                    item = parsed.model_dump()
                    item["stream_id"] = stream_ids.get((item["stream_code"] or "").upper())
                    item["current_training_stage_id"] = stage_ids.get((item["current_training_stage_code"] or "").upper())
                    item["batch_id"] = batch_ids.get((item["batch_code"] or "").upper())
                    pending.append(item)
                elif upload_type == "ASSESSMENTS":
                    projected = _project_row(row, REQUIRED_ASSESSMENT_FIELDS)
                    parsed = AssessmentRow.model_validate(projected)
                    item = parsed.model_dump()
                    trainee_id = trainee_ids.get(item["employee_id"].upper())
                    if not trainee_id:
                        raise ValueError("employee_id not found")
                    item["trainee_id"] = trainee_id
                    item.pop("employee_id", None)
                    pending.append(item)
                elif upload_type == "STAGES":
                    projected = _project_row(row, REQUIRED_STAGE_FIELDS)
                    parsed = StageRow.model_validate(projected)
                    item = parsed.model_dump()
                    trainee_id = trainee_ids.get(item["employee_id"].upper())
                    if not trainee_id:
                        raise ValueError("employee_id not found")
                    stage_type_id = stage_ids.get(item["stage_code"].upper())
                    if not stage_type_id:
                        raise ValueError("stage_code not found")
                    item["trainee_id"] = trainee_id
                    item["stage_type_id"] = stage_type_id
                    item["updated_by_user_id"] = uuid.UUID(message["requested_by_user_id"])
                    item.pop("employee_id", None)
                    item.pop("stage_code", None)
                    pending.append(item)
                elif upload_type == "COMPETENCY":
                    projected = _project_row(row, REQUIRED_COMPETENCY_FIELDS)
                    parsed = CompetencyRow.model_validate(projected)
                    item = parsed.model_dump()
                    trainee_id = trainee_ids.get(item["employee_id"].upper())
                    if not trainee_id:
                        raise ValueError("employee_id not found")
                    item["trainee_id"] = trainee_id
                    item.pop("employee_id", None)
                    pending.append(item)
                else:
                    raise ValueError(f"Unsupported upload_type: {upload_type}")
            except (ValidationError, ValueError) as exc:
                errors.append(
                    {
                        "row_number": row_number,
                        "column_name": None,
                        "message": str(exc),
                        "raw_payload": row,
                    }
                )
                continue

            if len(pending) >= batch_size:
                _process_batch(db=db, upload_type=upload_type, processed=pending)
                success_count += len(pending)
                pending = []
                db.flush()

        if pending:
            _process_batch(db=db, upload_type=upload_type, processed=pending)
            success_count += len(pending)
            db.flush()

        _insert_errors(db, upload_id, errors)
        _mark_status(
            db,
            upload_id,
            "COMPLETED",
            row_count=row_count,
            success_count=success_count,
            error_count=len(errors),
        )
        db.commit()
        completion_message = {
            "message_id": str(uuid.uuid4()),
            "upload_id": str(upload_id),
            "upload_type": upload_type,
            "status": "COMPLETED",
            "success_count": success_count,
            "error_count": len(errors),
            "completed_at": datetime.now(UTC).isoformat(),
        }
        settings = get_settings()
        get_queue_client().publish(
            queue_name=settings.queue_name_ingestion_completed,
            message=completion_message,
            message_id=completion_message["message_id"],
        )
    except Exception:
        db.rollback()
        _mark_status(db, upload_id, "FAILED")
        db.commit()
        raise
    finally:
        db.close()
