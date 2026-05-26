"""Admin API schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ScoringConfigRead(BaseModel):
    id: uuid.UUID
    version: int
    is_active: bool
    weights: dict[str, Any]
    high_threshold: Decimal
    average_threshold: Decimal
    effective_from: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoringConfigCreate(BaseModel):
    weights: dict[str, float]
    high_threshold: Decimal = Field(default=Decimal("75"))
    average_threshold: Decimal = Field(default=Decimal("50"))


class TopperRuleRead(BaseModel):
    id: uuid.UUID
    topper_type: str
    scope_field: str | None
    metric: str
    top_n: int | None
    top_percent: Decimal | None
    min_score: Decimal | None
    is_active: bool
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TopperRuleCreate(BaseModel):
    topper_type: str
    scope_field: str | None = None
    metric: str = "composite_score"
    top_n: int | None = 5
    top_percent: Decimal | None = None
    min_score: Decimal | None = None


class TopperRuleUpdate(BaseModel):
    scope_field: str | None = None
    metric: str | None = None
    top_n: int | None = None
    top_percent: Decimal | None = None
    min_score: Decimal | None = None
    is_active: bool | None = None


class ClassificationOverrideCreate(BaseModel):
    employee_id: str
    override_classification: str
    reason: str | None = None
    expires_at: datetime | None = None


class ClassificationOverrideRead(BaseModel):
    id: uuid.UUID
    trainee_id: uuid.UUID
    override_classification: str
    reason: str | None
    created_by_user_id: uuid.UUID
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserPatch(BaseModel):
    is_active: bool | None = None
    role_name: str | None = None


class UploadMonitorItem(BaseModel):
    id: uuid.UUID
    upload_type: str
    file_name: str
    status: str
    row_count: int | None
    success_count: int | None
    error_count: int | None
    uploaded_by: str | None
    created_at: datetime
    error_report_url: str | None

    model_config = {"from_attributes": True}


class UploadRowErrorRead(BaseModel):
    row_number: int
    column_name: str | None
    message: str

    model_config = {"from_attributes": True}


class AuditLogRead(BaseModel):
    id: uuid.UUID
    action: str
    entity_type: str
    entity_id: str | None
    actor_user_id: uuid.UUID | None
    new_values: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecomputeResponse(BaseModel):
    classifications_updated: int
    topper_flags_created: int
