from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.db_bind import SQL_CURRENT_TIMESTAMP, prepare_rows_for_db

logger = logging.getLogger(__name__)

_TS = SQL_CURRENT_TIMESTAMP


def upsert_trainees(db: Session, rows: list[dict]) -> None:
    if not rows:
        return
    logger.info("upserter: trainees rows=%s", len(rows))
    stmt = text(
        f"""
        INSERT INTO trainees (
            id, employee_id, superset_id, doj, full_name, gender, email, phone,
            college_name, college_city, college_state, base_location, current_training_location,
            training_status, stream_id, current_training_stage_id, category, assigned_competency,
            batch_id, is_active, created_at, updated_at
        ) VALUES (
            :id, :employee_id, :superset_id, :doj, :full_name, :gender, :email, :phone,
            :college_name, :college_city, :college_state, :base_location, :current_training_location,
            :training_status, :stream_id, :current_training_stage_id, :category, :assigned_competency,
            :batch_id, true, {_TS}, {_TS}
        )
        ON CONFLICT (employee_id) DO UPDATE SET
            superset_id = EXCLUDED.superset_id,
            doj = EXCLUDED.doj,
            full_name = EXCLUDED.full_name,
            gender = EXCLUDED.gender,
            email = EXCLUDED.email,
            phone = EXCLUDED.phone,
            college_name = EXCLUDED.college_name,
            college_city = EXCLUDED.college_city,
            college_state = EXCLUDED.college_state,
            base_location = EXCLUDED.base_location,
            current_training_location = EXCLUDED.current_training_location,
            training_status = EXCLUDED.training_status,
            stream_id = EXCLUDED.stream_id,
            current_training_stage_id = EXCLUDED.current_training_stage_id,
            category = EXCLUDED.category,
            assigned_competency = EXCLUDED.assigned_competency,
            batch_id = EXCLUDED.batch_id,
            is_active = true,
            updated_at = {_TS}
        """
    )
    db.execute(stmt, prepare_rows_for_db(rows))


def upsert_assessments(db: Session, rows: list[dict]) -> None:
    if not rows:
        return
    logger.info("upserter: assessments rows=%s", len(rows))
    stmt = text(
        f"""
        INSERT INTO assessments (
            id, trainee_id, program, assessment_code, attempt_no, score, max_score,
            assessment_date, remarks, created_at, updated_at
        ) VALUES (
            :id, :trainee_id, :program, :assessment_code, :attempt_no, :score, :max_score,
            :assessment_date, :remarks, {_TS}, {_TS}
        )
        ON CONFLICT (trainee_id, assessment_code, attempt_no) DO UPDATE SET
            program = EXCLUDED.program,
            score = EXCLUDED.score,
            max_score = EXCLUDED.max_score,
            assessment_date = EXCLUDED.assessment_date,
            remarks = EXCLUDED.remarks,
            updated_at = {_TS}
        """
    )
    db.execute(stmt, prepare_rows_for_db(rows))


def upsert_stages(db: Session, rows: list[dict]) -> None:
    if not rows:
        return
    logger.info("upserter: training_stages rows=%s", len(rows))
    stmt = text(
        f"""
        INSERT INTO training_stages (
            id, trainee_id, stage_type_id, status, score, attempts, completion_date,
            updated_by_user_id, updated_at
        ) VALUES (
            :id, :trainee_id, :stage_type_id, :status, :score, :attempts, :completion_date,
            :updated_by_user_id, {_TS}
        )
        ON CONFLICT (trainee_id, stage_type_id) DO UPDATE SET
            status = EXCLUDED.status,
            score = EXCLUDED.score,
            attempts = EXCLUDED.attempts,
            completion_date = EXCLUDED.completion_date,
            updated_by_user_id = EXCLUDED.updated_by_user_id,
            updated_at = {_TS}
        """
    )
    db.execute(stmt, prepare_rows_for_db(rows))


def upsert_competencies(db: Session, rows: list[dict]) -> None:
    if not rows:
        return
    logger.info("upserter: trainee_competencies rows=%s", len(rows))
    stmt = text(
        f"""
        INSERT INTO trainee_competencies (
            id, trainee_id, competency_name, status, skill_level, readiness_flag,
            completion_date, updated_at
        ) VALUES (
            :id, :trainee_id, :competency_name, :status, :skill_level, :readiness_flag,
            :completion_date, {_TS}
        )
        ON CONFLICT (trainee_id, competency_name) DO UPDATE SET
            status = EXCLUDED.status,
            skill_level = EXCLUDED.skill_level,
            readiness_flag = EXCLUDED.readiness_flag,
            completion_date = EXCLUDED.completion_date,
            updated_at = {_TS}
        """
    )
    db.execute(stmt, prepare_rows_for_db(rows))
