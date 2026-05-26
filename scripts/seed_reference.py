"""Reference data (roles, stages, streams, assessment catalog) — same as Alembic 003.

Used when initializing SQLite via ORM `create_all`; PostgreSQL should use `alembic upgrade head`.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.reference import AssessmentCatalog, Stream, TrainingStageType
from models.user import Role


def seed_reference_data(session: Session) -> None:
    _seed_roles(session)
    _seed_training_stage_types(session)
    _seed_streams(session)
    _seed_assessment_catalog(session)
    _seed_automation_defaults(session)
    session.commit()


def _seed_automation_defaults(session: Session) -> None:
    from services.scoring_service import ensure_default_scoring_config
    from services.topper_service import ensure_default_topper_rules

    ensure_default_scoring_config(session)
    ensure_default_topper_rules(session)


def _seed_roles(session: Session) -> None:
    rows = [
        ("training_coordinator", "Bulk upload and stage updates"),
        ("trainer", "Review trainee performance"),
        ("hr", "Training outcomes and insights"),
        ("business_head", "Dashboards and effectiveness"),
        ("system_admin", "Users, config, audit"),
    ]
    for name, description in rows:
        if session.execute(select(Role.id).where(Role.name == name)).scalar_one_or_none():
            continue
        session.add(Role(name=name, description=description))


def _seed_training_stage_types(session: Session) -> None:
    rows = [
        ("SPARK", "Spark", 1),
        ("FOUNDATION", "Foundation", 2),
        ("CODING_TEST", "Coding Test", 3),
        ("PROJECT", "Project", 4),
        ("COMPETENCY_TRAINING", "Competency Training", 5),
    ]
    for code, label, sort_order in rows:
        if session.execute(select(TrainingStageType.id).where(TrainingStageType.code == code)).scalar_one_or_none():
            continue
        session.add(
            TrainingStageType(code=code, label=label, sort_order=sort_order, is_active=True)
        )


def _seed_streams(session: Session) -> None:
    rows = [
        ("JAVA", "Java"),
        ("PYTHON", "Python"),
        ("DATA", "Data"),
        ("QA", "QA"),
        ("CLOUD", "Cloud"),
    ]
    for code, label in rows:
        if session.execute(select(Stream.id).where(Stream.code == code)).scalar_one_or_none():
            continue
        session.add(
            Stream(
                code=code,
                label=label,
                is_active=True,
            )
        )


def _seed_assessment_catalog(session: Session) -> None:
    rows: list[tuple[str, str, str, float, int]] = [
        ("SPARK_P1_A1", "SPARK", "Spark Phase 1 – Attempt 1", 100, 1),
        ("SPARK_P1_A2", "SPARK", "Spark Phase 1 – Attempt 2", 100, 2),
        ("SPARK_FINAL", "SPARK", "Spark Final Score", 100, 3),
        ("FM1", "FOUNDATION", "Foundation Module 1", 100, 10),
        ("FM2", "FOUNDATION", "Foundation Module 2", 100, 11),
        ("FM3", "FOUNDATION", "Foundation Module 3", 100, 12),
        ("SQL", "TECHNICAL", "SQL", 100, 20),
        ("JAVA", "TECHNICAL", "Java", 100, 21),
        ("PYTHON", "TECHNICAL", "Python", 100, 22),
        ("PROJECT", "PROJECT", "Project score", 100, 30),
        ("PROJECT_MENTOR", "PROJECT", "Mentor evaluation", 100, 31),
        ("SA1", "SOFT_SKILL", "SA1", 100, 40),
        ("SA2", "SOFT_SKILL", "SA2", 100, 41),
        ("SA3", "SOFT_SKILL", "SA3", 100, 42),
        ("SA4", "SOFT_SKILL", "SA4", 100, 43),
        ("SA5", "SOFT_SKILL", "SA5", 100, 44),
        ("SA6", "SOFT_SKILL", "SA6", 100, 45),
        ("SP1", "SOFT_SKILL", "SP1", 100, 46),
        ("SP2", "SOFT_SKILL", "SP2", 100, 47),
        ("CT1", "CODING_TEST", "Coding Test 1", 100, 50),
        ("CT2", "CODING_TEST", "Coding Test 2", 100, 51),
        ("CT3", "CODING_TEST", "Coding Test 3", 100, 52),
        ("CT4", "CODING_TEST", "Coding Test 4", 100, 53),
        ("CT5", "CODING_TEST", "Coding Test 5", 100, 54),
        ("CT6", "CODING_TEST", "Coding Test 6", 100, 55),
        ("CT7", "CODING_TEST", "Coding Test 7", 100, 56),
    ]
    for code, program, label, mx, ord_ in rows:
        if session.execute(select(AssessmentCatalog.id).where(AssessmentCatalog.code == code)).scalar_one_or_none():
            continue
        session.add(
            AssessmentCatalog(
                code=code,
                program=program,
                label=label,
                default_max_score=Decimal(str(mx)),
                display_order=ord_,
                is_active=True,
            )
        )
