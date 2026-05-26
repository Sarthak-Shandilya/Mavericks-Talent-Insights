"""Tests for report generation."""
from __future__ import annotations

from services.scoring_service import classify_trainee
from services.reports_service import batch_performance
from schemas.reports import ReportFilters
from models.trainee import Assessment
from datetime import date


def test_batch_performance_report_empty(db_session):
    report = batch_performance(db_session, ReportFilters(format="json"))
    assert report.generated_at is not None
    assert isinstance(report.rows, list)


def test_batch_performance_with_data(sample_trainee, db_session):
    db_session.add(
        Assessment(
            trainee_id=sample_trainee.id,
            program="SPARK",
            assessment_code="SPARK_P1_A1",
            attempt_no=1,
            score=80,
            max_score=100,
            assessment_date=date.today(),
        )
    )
    db_session.commit()
    classify_trainee(db_session, sample_trainee.id)
    db_session.commit()
    report = batch_performance(db_session, ReportFilters(format="json"))
    assert len(report.rows) >= 1
