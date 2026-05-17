from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.engine.url import make_url

from configs.settings import get_settings
from db.session import SessionLocal
from parsers.excel_reader import iter_rows
from processors import upserter
from storage import get_storage_client
from utils.db_bind import bind_sqlite_params, bind_sqlite_rows
from utils.queue_clients import get_queue_client
from validators.row_schemas import AssessmentRow, CompetencyRow, StageRow, TraineeMasterRow

logger = logging.getLogger(__name__)

REQUIRED_TRAINEE_FIELDS = {
    "employee_id": ("employee_id", "employeeid", "emp_id", "employee_code", "emp_code"),
    "superset_id": ("superset_id", "supersetid", "superset"),
    "doj": ("doj", "date_of_joining", "joining_date", "date_of_join"),
    "full_name": ("full_name", "name", "trainee_name", "employee_name", "candidate_name"),
    "gender": ("gender", "sex"),
    "email": ("email", "email_id", "e_mail", "work_email", "official_email"),
    "phone": ("phone", "phone_number", "mobile", "mobile_number", "contact_number", "contact"),
    "college_name": ("college_name", "institute_name", "university_name"),
    "college_city": ("college_city", "college_location_city", "institute_city"),
    "college_state": ("college_state", "college_location_state", "institute_state"),
    "base_location": ("base_location", "home_location", "home_base"),
    "current_training_location": ("current_training_location", "training_location", "training_site"),
    "training_status": ("training_status", "status"),
    "stream_code": ("stream", "stream_code", "technology_stream"),
    "current_training_stage_code": (
        "current_training_stage_code",
        "current_training_stage",
        "training_stage",
        "stage",
        "stage_code",
        "current_stage",
    ),
    "category": ("category", "trainee_category"),
    "assigned_competency": ("assigned_competency", "competency", "competency_track", "track"),
    "batch_code": ("batch_code", "batch", "batch_id", "batch_name"),
}

REQUIRED_ASSESSMENT_FIELDS = {
    "employee_id": ("employee_id", "employeeid", "emp_id"),
    "program": ("program", "program_name", "assessment_program"),
    "assessment_code": ("assessment_code", "code", "test_code", "assessment", "test"),
    "attempt_no": ("attempt_no", "attempt", "attempt_number", "try_no"),
    "score": ("score", "marks", "obtained_score"),
    "max_score": ("max_score", "maximum_score", "total_marks", "out_of"),
    "assessment_date": ("assessment_date", "date", "test_date", "exam_date"),
    "remarks": ("remarks", "comments", "notes", "feedback"),
}

REQUIRED_STAGE_FIELDS = {
    "employee_id": ("employee_id", "employeeid", "emp_id"),
    "stage_code": ("stage_code", "stage", "current_training_stage", "training_stage_code"),
    "status": ("status", "stage_status"),
    "score": ("score", "stage_score", "marks"),
    "attempts": ("attempts", "no_of_attempts", "attempt_count"),
    "completion_date": ("completion_date", "completed_on", "finish_date"),
}

REQUIRED_COMPETENCY_FIELDS = {
    "employee_id": ("employee_id", "employeeid", "emp_id"),
    "competency_name": ("competency_name", "assigned_competency", "competency", "track"),
    "status": ("status", "competency_status"),
    "skill_level": ("skill_level", "level", "proficiency"),
    "readiness_flag": ("readiness_flag", "readiness", "ready", "is_ready", "deployment_ready"),
    "completion_date": ("completion_date", "completed_on"),
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
    return {str(row[0]).upper(): bind_sqlite_params({"v": row[1]})["v"] for row in rows}


def _fetch_trainee_id_map(db) -> dict[str, Any]:
    rows = db.execute(text("SELECT employee_id, id FROM trainees")).all()
    return {
        str(row[0]).upper(): bind_sqlite_params({"v": row[1]})["v"]
        for row in rows
    }


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
            bind_sqlite_params(
                {
                    "id": uuid.uuid4(),
                    "upload_id": upload_id,
                    "row_number": err["row_number"],
                    "column_name": err.get("column_name"),
                    "message": err["message"],
                    "raw_payload": err.get("raw_payload"),
                }
            )
        )
    db.execute(stmt, payload)


def _safe_database_url() -> str:
    """Log-friendly DSN (password hidden)."""
    try:
        return make_url(get_settings().database_url).render_as_string(hide_password=True)
    except Exception:
        return "<could not parse DATABASE_URL>"


def _mark_status(db, upload_id: uuid.UUID, status: str, **fields: Any) -> None:
    parts = ["status = :status"]
    params: dict[str, Any] = {"upload_id": upload_id, "status": status}
    for key, value in fields.items():
        parts.append(f"{key} = :{key}")
        params[key] = value
    if status in ("COMPLETED", "FAILED"):
        parts.append("completed_at = :completed_at")
        params["completed_at"] = datetime.now(UTC)
    stmt = text(f"UPDATE upload_batches SET {', '.join(parts)} WHERE id = :upload_id")
    db.execute(stmt, bind_sqlite_params(params))


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
    settings = get_settings()
    batch_size = settings.ingestion_batch_size
    storage = get_storage_client()

    logger.info(
        "ingestion start upload_id=%s upload_type=%s batch_size=%s db=%s storage=%s",
        upload_id,
        upload_type,
        batch_size,
        _safe_database_url(),
        settings.storage_type,
    )
    logger.info("queue message file_url=%s", message.get("file_url"))

    db = SessionLocal()
    try:
        logger.info("db: marking PROCESSING upload_id=%s", upload_id)
        _mark_status(db, upload_id, "PROCESSING")
        db.commit()
        logger.info("db: PROCESSING committed upload_id=%s", upload_id)

        logger.info("storage: reading file_url=%s", message["file_url"])
        payload = storage.read_bytes(url=message["file_url"])
        logger.info("storage: read %s bytes", len(payload))

        logger.info("db: loading reference maps (trainees, streams, stages, batches)")
        trainee_ids = _fetch_trainee_id_map(db)
        stream_ids = _fetch_map(db, "SELECT code, id FROM streams")
        stage_ids = _fetch_map(db, "SELECT code, id FROM training_stage_types")
        batch_ids = _fetch_map(db, "SELECT code, id FROM batches")
        logger.info(
            "db: maps sizes trainees=%s streams=%s stages=%s batches=%s",
            len(trainee_ids),
            len(stream_ids),
            len(stage_ids),
            len(batch_ids),
        )

        pending: list[dict] = []
        errors: list[dict] = []
        success_count = 0
        row_count = 0

        logger.info("excel: iterating rows upload_id=%s", upload_id)
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
                    item["updated_by_user_id"] = str(
                        uuid.UUID(message["requested_by_user_id"])
                    )
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
                logger.info(
                    "db: upsert batch upload_id=%s size=%s (batch_size limit)",
                    upload_id,
                    len(pending),
                )
                _process_batch(db=db, upload_type=upload_type, processed=pending)
                success_count += len(pending)
                pending = []
                db.flush()

        if pending:
            logger.info("db: upsert final batch upload_id=%s size=%s", upload_id, len(pending))
            _process_batch(db=db, upload_type=upload_type, processed=pending)
            success_count += len(pending)
            db.flush()

        logger.info(
            "db: row scan done upload_id=%s row_count=%s success=%s errors=%s",
            upload_id,
            row_count,
            success_count,
            len(errors),
        )
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
        logger.info("db: COMPLETED committed upload_id=%s", upload_id)
        completion_message = {
            "message_id": str(uuid.uuid4()),
            "upload_id": str(upload_id),
            "upload_type": upload_type,
            "status": "COMPLETED",
            "success_count": success_count,
            "error_count": len(errors),
            "completed_at": datetime.now(UTC).isoformat(),
        }
        get_queue_client().publish(
            queue_name=settings.queue_name_ingestion_completed,
            message=completion_message,
            message_id=completion_message["message_id"],
        )
        logger.info(
            "ingestion done upload_id=%s published completion queue=%s",
            upload_id,
            settings.queue_name_ingestion_completed,
        )
    except Exception:
        logger.exception(
            "ingestion FAILED upload_id=%s upload_type=%s — "
            "if you see DB connection refused, set DATABASE_URL to the SAME database as the API "
            "(e.g. sqlite:///../../mavericks.db when API uses sqlite:///./mavericks.db).",
            upload_id,
            upload_type,
        )
        try:
            db.rollback()
        except Exception:
            logger.warning("db: rollback failed upload_id=%s", upload_id, exc_info=True)
        try:
            fail_db = SessionLocal()
            try:
                _mark_status(fail_db, upload_id, "FAILED")
                fail_db.commit()
                logger.info("db: FAILED status persisted upload_id=%s", upload_id)
            finally:
                fail_db.close()
        except Exception:
            logger.exception(
                "db: could not persist FAILED for upload_id=%s (check DATABASE_URL matches API)",
                upload_id,
            )
        raise
    finally:
        db.close()
        logger.info("db: session closed upload_id=%s", upload_id)