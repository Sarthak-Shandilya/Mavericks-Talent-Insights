from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Stream(Base):
    __tablename__ = "streams"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    trainees: Mapped[list["Trainee"]] = relationship(back_populates="stream")


class TrainingStageType(Base):
    """Canonical pipeline stages from BRD §7.2."""

    __tablename__ = "training_stage_types"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    trainee_stage_rows: Mapped[list["TraineeStage"]] = relationship(back_populates="stage_type")


class AssessmentCatalog(Base):
    """Valid assessment codes for ingest validation (BRD §7.3)."""

    __tablename__ = "assessment_catalog"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    program: Mapped[str] = mapped_column(String(32), nullable=False)  # AssessmentProgram value
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_max_score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False, default=100)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
