"""Trainer, HR, and Business Head dashboard schemas."""
from __future__ import annotations

from pydantic import BaseModel


class StakeholderDashboardRequest(BaseModel):
    pass


class TrainerDashboardResponse(BaseModel):
    total_trainees: int
    high_performers: int
    low_performers: int
    avg_score: float


class TraineeSummaryItem(BaseModel):
    employee_id: str
    full_name: str
    batch: str | None
    stream: str | None
    performance: str | None
    current_stage: str | None


class HRDashboardResponse(BaseModel):
    total_active: int
    completion_rate: float
    competency_ready_count: int
    avg_performance: float


class DemographicsRow(BaseModel):
    dimension: str
    value: str
    count: int


class DemographicsResponse(BaseModel):
    rows: list[DemographicsRow]


class BusinessHeadDashboardResponse(BaseModel):
    total_batches: int
    total_trainees: int
    overall_avg_score: float
    topper_count: int


class StreamTrendRow(BaseModel):
    stream: str
    trainee_count: int
    avg_score: float


class StreamTrendsResponse(BaseModel):
    rows: list[StreamTrendRow]


class TopperSummaryRow(BaseModel):
    topper_type: str
    count: int


class TopperSummaryResponse(BaseModel):
    rows: list[TopperSummaryRow]
