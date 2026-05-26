"""Pytest fixtures."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import models  # noqa: F401
from models.automation import ScoringConfig
from models.base import Base
from models.reference import Stream, TrainingStageType
from models.trainee import Assessment, Batch, Trainee
from scripts.seed_reference import seed_reference_data


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        seed_reference_data(session)
        yield session


@pytest.fixture()
def sample_trainee(db_session: Session) -> Trainee:
    from sqlalchemy import select

    stream = db_session.execute(select(Stream).where(Stream.code == "JAVA")).scalar_one()
    stage = db_session.execute(
        select(TrainingStageType).where(TrainingStageType.code == "SPARK")
    ).scalar_one()
    batch = Batch(code="B2026-01", name="Batch Jan 2026")
    db_session.add(batch)
    db_session.flush()
    trainee = Trainee(
        employee_id="EMP001",
        superset_id="SS001",
        doj=date(2026, 1, 1),
        full_name="Test User",
        gender="M",
        email="test@example.com",
        phone="9999999999",
        college_name="Test College",
        college_city="Chennai",
        college_state="TN",
        base_location="Chennai",
        current_training_location="Chennai",
        training_status="ACTIVE",
        stream_id=stream.id,
        current_training_stage_id=stage.id,
        category="A",
        assigned_competency="Java Dev",
        batch_id=batch.id,
    )
    db_session.add(trainee)
    db_session.commit()
    return trainee
