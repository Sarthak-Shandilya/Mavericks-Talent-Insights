from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Trainee(Base):
    __tablename__ = "trainees"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(64), nullable=False)
    superset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    doj: Mapped[date] = mapped_column(Date, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    college_name: Mapped[str] = mapped_column(String(512), nullable=False)
    college_city: Mapped[str] = mapped_column(String(255), nullable=False)
    college_state: Mapped[str] = mapped_column(String(255), nullable=False)
    base_location: Mapped[str] = mapped_column(String(255), nullable=False)
    current_training_location: Mapped[str] = mapped_column(String(255), nullable=False)
    training_status: Mapped[str] = mapped_column(String(32), nullable=False)
    stream_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("streams.id"))
    current_training_stage_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("training_stage_types.id"))
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    assigned_competency: Mapped[str] = mapped_column(String(255), nullable=False)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("batches.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    trainee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("trainees.id"), nullable=False)
    program: Mapped[str] = mapped_column(String(32), nullable=False)
    assessment_code: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    assessment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class TraineeStage(Base):
    __tablename__ = "training_stages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    trainee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("trainees.id"), nullable=False)
    stage_type_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("training_stage_types.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)


class TraineeCompetency(Base):
    __tablename__ = "trainee_competencies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    trainee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("trainees.id"), nullable=False)
    competency_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    skill_level: Mapped[str] = mapped_column(String(32), nullable=False)
    readiness_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
