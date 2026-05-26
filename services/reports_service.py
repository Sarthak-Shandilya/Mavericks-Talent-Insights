"""BRD §7.8 structured reports with JSON/Excel/PDF export."""
from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

from fastapi import HTTPException, Response, status
from openpyxl import Workbook
from sqlalchemy.orm import Session

import repositories.reports_repository as repo
from schemas.reports import (
    AssessmentTrendReport,
    BatchPerformanceReport,
    BatchPerformanceRow,
    CompetencyReadinessReport,
    CompetencyReadinessRow,
    ReportFilters,
    StageProgressReport,
    StageProgressRow,
    TopperReport,
    TopperRow,
    TraineePerformanceReport,
    AssessmentScoreItem,
    AssessmentTrendPoint,
)

def _table_to_pdf(title: str, headers: list[str], rows: list[list[str]]) -> bytes:
    from services.pdf_export import table_to_pdf
    return table_to_pdf(title, headers, rows)

_NOW = lambda: datetime.now(UTC)


def _excel_response(filename: str, headers: list[str], rows: list[list]) -> Response:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _pdf_response(filename: str, title: str, headers: list[str], rows: list[list]) -> Response:
    content = _table_to_pdf(title, headers, [[str(c) for c in r] for r in rows])
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def batch_performance(db: Session, filters: ReportFilters):
    raw = repo.batch_performance_rows(db, filters)
    report = BatchPerformanceReport(
        rows=[BatchPerformanceRow(**r) for r in raw],
        generated_at=_NOW(),
    )
    if filters.format == "json":
        return report
    headers = ["batch_code", "batch_name", "total", "avg_score", "high", "avg_band", "low", "completion_%"]
    rows = [
        [r.batch_code, r.batch_name, r.total_trainees, r.avg_score, r.high_count, r.average_count, r.low_count, r.completion_rate]
        for r in report.rows
    ]
    if filters.format == "xlsx":
        return _excel_response("batch_performance.xlsx", headers, rows)
    return _pdf_response("batch_performance.pdf", "Batch Performance Report", headers, rows)


def trainee_performance(db: Session, filters: ReportFilters):
    eid = filters.employee_id
    if not eid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="employee_id required")
    t = repo.trainee_performance_detail(db, eid)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trainee not found")
    pc = t.performance_classification
    report = TraineePerformanceReport(
        employee_id=t.employee_id,
        full_name=t.full_name,
        batch_code=t.batch.code if t.batch else None,
        stream=t.stream.code if t.stream else None,
        current_stage=t.current_training_stage.code if t.current_training_stage else None,
        classification=pc.classification if pc else None,
        composite_score=float(pc.composite_score) if pc and pc.composite_score else None,
        assessments=[
            AssessmentScoreItem(
                assessment_code=a.assessment_code,
                program=a.program,
                attempt_no=a.attempt_no,
                score=float(a.score),
                max_score=float(a.max_score),
                assessment_date=a.assessment_date,
            )
            for a in t.assessments
        ],
        stages=[
            {"stage": s.stage_type.code if s.stage_type else None, "status": s.status, "score": float(s.score) if s.score else None}
            for s in t.stage_rows
        ],
        competencies=[
            {"name": c.competency_name, "status": c.status, "skill_level": c.skill_level, "ready": c.readiness_flag}
            for c in t.competencies
        ],
        topper_flags=[
            {"type": f.topper_type, "scope": f.scope_value, "rank": f.rank}
            for f in t.topper_flags
        ],
    )
    if filters.format == "json":
        return report
    headers = ["code", "program", "attempt", "score", "max"]
    rows = [[a.assessment_code, a.program, a.attempt_no, a.score, a.max_score] for a in report.assessments]
    if filters.format == "xlsx":
        return _excel_response(f"trainee_{eid}.xlsx", headers, rows)
    return _pdf_response(f"trainee_{eid}.pdf", f"Trainee Report: {t.full_name}", headers, rows)


def stage_progress(db: Session, filters: ReportFilters):
    raw = repo.stage_progress_rows(db, filters)
    report = StageProgressReport(
        rows=[StageProgressRow(**r) for r in raw],
        generated_at=_NOW(),
    )
    if filters.format == "json":
        return report
    headers = ["stage", "label", "completed", "pending", "n/a", "avg_score"]
    rows = [[r.stage_code, r.stage_label, r.completed, r.pending, r.not_applicable, r.avg_score] for r in report.rows]
    if filters.format == "xlsx":
        return _excel_response("stage_progress.xlsx", headers, rows)
    return _pdf_response("stage_progress.pdf", "Stage Progress Report", headers, rows)


def toppers(db: Session, filters: ReportFilters):
    raw = repo.topper_rows(db, filters)
    report = TopperReport(
        rows=[TopperRow(**r) for r in raw],
        generated_at=_NOW(),
    )
    if filters.format == "json":
        return report
    headers = ["employee_id", "name", "type", "scope", "rank", "score"]
    rows = [[r.employee_id, r.full_name, r.topper_type, r.scope_value, r.rank, r.composite_score] for r in report.rows]
    if filters.format == "xlsx":
        return _excel_response("toppers.xlsx", headers, rows)
    return _pdf_response("toppers.pdf", "Topper Analysis", headers, rows)


def competency_readiness(db: Session, filters: ReportFilters):
    raw = repo.competency_readiness_rows(db, filters)
    report = CompetencyReadinessReport(
        rows=[CompetencyReadinessRow(**r) for r in raw],
        generated_at=_NOW(),
    )
    if filters.format == "json":
        return report
    headers = ["competency", "total", "completed", "in_progress", "ready"]
    rows = [[r.competency_name, r.total, r.completed, r.in_progress, r.ready_count] for r in report.rows]
    if filters.format == "xlsx":
        return _excel_response("competency_readiness.xlsx", headers, rows)
    return _pdf_response("competency_readiness.pdf", "Competency Readiness", headers, rows)


def assessment_trends(db: Session, filters: ReportFilters):
    raw = repo.assessment_trend_points(db, filters)
    report = AssessmentTrendReport(
        points=[AssessmentTrendPoint(**p) for p in raw],
        generated_at=_NOW(),
    )
    if filters.format == "json":
        return report
    headers = ["employee_id", "code", "attempt", "score", "max", "date"]
    rows = [[p.employee_id, p.assessment_code, p.attempt_no, p.score, p.max_score, p.assessment_date] for p in report.points]
    if filters.format == "xlsx":
        return _excel_response("assessment_trends.xlsx", headers, rows)
    return _pdf_response("assessment_trends.pdf", "Assessment Trends", headers, rows)
