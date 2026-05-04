from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.trainee import Trainee


class ScoringConfig(Base):
    __tablename__ = "scoring_configs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weights: Mapped[dict] = mapped_column(JSON, nullable=False)
    high_threshold: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    average_threshold: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    classifications: Mapped[list[PerformanceClassification]] = relationship(
        back_populates="scoring_config"
    )


class TopperRule(Base):
    __tablename__ = "topper_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topper_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    scope_field: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    top_n: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    min_score: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    topper_flags: Mapped[list[TopperFlag]] = relationship(back_populates="rule")


class PerformanceClassification(Base):
    __tablename__ = "performance_classifications"
    __table_args__ = (UniqueConstraint("trainee_id", name="uq_performance_classifications_trainee"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("trainees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    composite_score: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    scoring_config_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scoring_configs.id"), nullable=True
    )
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trainee: Mapped[Trainee] = relationship(back_populates="performance_classification")
    scoring_config: Mapped[ScoringConfig | None] = relationship(back_populates="classifications")


class ClassificationOverride(Base):
    __tablename__ = "classification_overrides"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("trainees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    override_classification: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trainee: Mapped[Trainee] = relationship(back_populates="classification_overrides")


class TopperFlag(Base):
    __tablename__ = "topper_flags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("trainees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topper_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    scope_value: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("topper_rules.id"), nullable=True
    )
    rule_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    trainee: Mapped[Trainee] = relationship(back_populates="topper_flags")
    rule: Mapped[TopperRule | None] = relationship(back_populates="topper_flags")
