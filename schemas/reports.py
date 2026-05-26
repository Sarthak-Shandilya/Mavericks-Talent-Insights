"""Report API schemas (BRD §7.8)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class ReportFilters(BaseModel):
    batch_code: str | None = None
    stream: str | None = None
    stage_code: str | None = None
    location: str | None = None
    employee_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    format: Literal["json", "xlsx", "pdf"] = "json"


class BatchPerformanceRow(BaseModel):
    batch_code: str
    batch_name: str
    total_trainees: int
    avg_score: float
    high_count: int
    average_count: int
    low_count: int
    completion_rate: float


class BatchPerformanceReport(BaseModel):
    rows: list[BatchPerformanceRow]
    generated_at: datetime


class AssessmentScoreItem(BaseModel):
    assessment_code: str
    program: str
    attempt_no: int
    score: float
    max_score: float
    assessment_date: date | None


class TraineePerformanceReport(BaseModel):
    employee_id: str
    full_name: str
    batch_code: str | None
    stream: str | None
    current_stage: str | None
    classification: str | None
    composite_score: float | None
    assessments: list[AssessmentScoreItem]
    stages: list[dict]
    competencies: list[dict]
    topper_flags: list[dict]


class StageProgressRow(BaseModel):
    stage_code: str
    stage_label: str
    completed: int
    pending: int
    not_applicable: int
    avg_score: float | None


class StageProgressReport(BaseModel):
    rows: list[StageProgressRow]
    generated_at: datetime


class TopperRow(BaseModel):
    employee_id: str
    full_name: str
    topper_type: str
    scope_value: str | None
    rank: int | None
    composite_score: float | None


class TopperReport(BaseModel):
    rows: list[TopperRow]
    generated_at: datetime


class CompetencyReadinessRow(BaseModel):
    competency_name: str
    total: int
    completed: int
    in_progress: int
    ready_count: int


class CompetencyReadinessReport(BaseModel):
    rows: list[CompetencyReadinessRow]
    generated_at: datetime


class AssessmentTrendPoint(BaseModel):
    employee_id: str
    assessment_code: str
    attempt_no: int
    score: float
    max_score: float
    assessment_date: date | None


class AssessmentTrendReport(BaseModel):
    points: list[AssessmentTrendPoint]
    generated_at: datetime
