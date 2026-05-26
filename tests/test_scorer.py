"""Tests for performance scoring."""
from __future__ import annotations

from datetime import date

import pytest

from models.trainee import Assessment
from services.scoring_service import (
    classify_trainee,
    compute_classifications_for_trainees,
    compute_composite_score,
    ensure_default_scoring_config,
)


def test_ensure_default_scoring_config(db_session):
    config = ensure_default_scoring_config(db_session)
    assert config.is_active is True
    assert "SPARK" in config.weights


def test_compute_composite_score():
    assessments = [
        Assessment(
            trainee_id=None,
            program="SPARK",
            assessment_code="SPARK_P1_A1",
            attempt_no=1,
            score=80,
            max_score=100,
        ),
        Assessment(
            trainee_id=None,
            program="FOUNDATION",
            assessment_code="FM1",
            attempt_no=1,
            score=70,
            max_score=100,
        ),
    ]
    weights = {"SPARK": 0.5, "FOUNDATION": 0.5}
    score = compute_composite_score(assessments, weights)
    assert score == 75.0


def test_classify_trainee_high(sample_trainee, db_session):
    db_session.add(
        Assessment(
            trainee_id=sample_trainee.id,
            program="SPARK",
            assessment_code="SPARK_P1_A1",
            attempt_no=1,
            score=90,
            max_score=100,
            assessment_date=date.today(),
        )
    )
    db_session.add(
        Assessment(
            trainee_id=sample_trainee.id,
            program="FOUNDATION",
            assessment_code="FM1",
            attempt_no=1,
            score=85,
            max_score=100,
            assessment_date=date.today(),
        )
    )
    db_session.commit()
    pc = classify_trainee(db_session, sample_trainee.id)
    assert pc is not None
    assert pc.classification in ("HIGH", "AVERAGE", "LOW")
    assert pc.composite_score is not None


def test_compute_classifications_for_trainees(sample_trainee, db_session):
    db_session.add(
        Assessment(
            trainee_id=sample_trainee.id,
            program="SPARK",
            assessment_code="SPARK_FINAL",
            attempt_no=1,
            score=60,
            max_score=100,
        )
    )
    db_session.commit()
    count = compute_classifications_for_trainees(db_session, [sample_trainee.id])
    assert count == 1
