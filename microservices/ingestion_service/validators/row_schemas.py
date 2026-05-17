from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


class TraineeMasterRow(BaseModel):
    employee_id: str = Field(min_length=1, max_length=64)
    superset_id: str = Field(min_length=1, max_length=64)
    doj: date
    full_name: str = Field(min_length=1, max_length=255)
    gender: str = Field(min_length=1, max_length=32)
    email: str = Field(min_length=3, max_length=255)
    phone: str = Field(min_length=1, max_length=32)
    college_name: str = Field(min_length=1, max_length=512)
    college_city: str = Field(min_length=1, max_length=255)
    college_state: str = Field(min_length=1, max_length=255)
    base_location: str = Field(min_length=1, max_length=255)
    current_training_location: str = Field(min_length=1, max_length=255)
    training_status: str = Field(min_length=1, max_length=32)
    stream_code: str | None = Field(default=None, max_length=32)
    current_training_stage_code: str | None = Field(default=None, max_length=64)
    category: str = Field(min_length=1, max_length=128)
    assigned_competency: str = Field(min_length=1, max_length=255)
    batch_code: str | None = Field(default=None, max_length=64)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class AssessmentRow(BaseModel):
    employee_id: str = Field(min_length=1, max_length=64)
    program: str = Field(min_length=1, max_length=32)
    assessment_code: str = Field(min_length=1, max_length=64)
    attempt_no: int = Field(ge=1)
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    assessment_date: date | None = None
    remarks: str | None = None

    @model_validator(mode="after")
    def check_score(self) -> "AssessmentRow":
        if self.score > self.max_score:
            raise ValueError("score cannot exceed max_score")
        return self


class StageRow(BaseModel):
    employee_id: str = Field(min_length=1, max_length=64)
    stage_code: str = Field(min_length=1, max_length=64)
    status: str = Field(min_length=1, max_length=32)
    score: float | None = Field(default=None, ge=0)
    attempts: int = Field(default=0, ge=0)
    completion_date: date | None = None


class CompetencyRow(BaseModel):
    employee_id: str = Field(min_length=1, max_length=64)
    competency_name: str = Field(min_length=1, max_length=255)
    status: str = Field(min_length=1, max_length=32)
    skill_level: str = Field(min_length=1, max_length=32)
    readiness_flag: bool = False
    completion_date: date | None = None

    @field_validator("readiness_flag", mode="before")
    @classmethod
    def coerce_readiness_flag(cls, value: object) -> bool:
        if value is None or value == "":
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        text = str(value).strip().lower()
        if text in ("yes", "y", "true", "1", "t"):
            return True
        if text in ("no", "n", "false", "0", "f", "na", "n/a"):
            return False
        raise ValueError(f"Readiness must be Yes/No or true/false (got {value!r})")
