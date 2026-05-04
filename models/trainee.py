from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.reference import Stream, TrainingStageType
from models.user import User


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stream_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    trainees: Mapped[list[Trainee]] = relationship(back_populates="batch")


class Trainee(Base):
    __tablename__ = "trainees"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    superset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    doj: Mapped[date] = mapped_column(Date, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    college_name: Mapped[str] = mapped_column(String(512), nullable=False)
    college_city: Mapped[str] = mapped_column(String(255), nullable=False)
    college_state: Mapped[str] = mapped_column(String(255), nullable=False)
    base_location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    current_training_location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    training_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stream_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("streams.id"), nullable=True
    )
    current_training_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("training_stage_types.id"), nullable=True
    )
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    assigned_competency: Mapped[str] = mapped_column(String(255), nullable=False)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("batches.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    batch: Mapped[Batch | None] = relationship(back_populates="trainees")
    stream: Mapped[Stream | None] = relationship(back_populates="trainees")
    current_training_stage: Mapped[TrainingStageType | None] = relationship(
        foreign_keys=[current_training_stage_id],
    )
    stage_rows: Mapped[list[TraineeStage]] = relationship(
        back_populates="trainee",
        foreign_keys="TraineeStage.trainee_id",
    )
    assessments: Mapped[list[Assessment]] = relationship(back_populates="trainee")
    competencies: Mapped[list[TraineeCompetency]] = relationship(back_populates="trainee")
    performance_classification: Mapped["PerformanceClassification | None"] = relationship(
        "PerformanceClassification",
        back_populates="trainee",
        uselist=False,
    )
    classification_overrides: Mapped[list["ClassificationOverride"]] = relationship(
        "ClassificationOverride",
        back_populates="trainee",
    )
    topper_flags: Mapped[list["TopperFlag"]] = relationship(
        "TopperFlag",
        back_populates="trainee",
    )


class TraineeStage(Base):
    """Per-trainee progress row for one pipeline stage (BRD §7.2)."""

    __tablename__ = "training_stages"
    __table_args__ = (
        UniqueConstraint("trainee_id", "stage_type_id", name="uq_training_stages_trainee_stage"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("trainees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("training_stage_types.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    trainee: Mapped[Trainee] = relationship(
        back_populates="stage_rows",
        foreign_keys=[trainee_id],
    )
    stage_type: Mapped[TrainingStageType] = relationship(
        back_populates="trainee_stage_rows",
        foreign_keys=[stage_type_id],
    )
    updated_by: Mapped[User | None] = relationship(foreign_keys=[updated_by_user_id])


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        UniqueConstraint(
            "trainee_id",
            "assessment_code",
            "attempt_no",
            name="uq_assessments_trainee_code_attempt",
        ),
        CheckConstraint("score <= max_score", name="ck_assessments_score_le_max"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("trainees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    program: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    assessment_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    assessment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    trainee: Mapped[Trainee] = relationship(back_populates="assessments")


class TraineeCompetency(Base):
    __tablename__ = "trainee_competencies"
    __table_args__ = (
        UniqueConstraint("trainee_id", "competency_name", name="uq_trainee_competency_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("trainees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    competency_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    skill_level: Mapped[str] = mapped_column(String(32), nullable=False)
    readiness_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    trainee: Mapped[Trainee] = relationship(back_populates="competencies")
