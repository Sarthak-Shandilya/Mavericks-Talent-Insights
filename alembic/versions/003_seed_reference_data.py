"""Seed roles, training stage types, streams, assessment catalog (BRD §7.2–7.3).

Revision ID: 003_seed_reference_data
Revises: 002_automation_upload_audit
Create Date: 2026-02-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_seed_reference_data"
down_revision: Union[str, Sequence[str], None] = "002_automation_upload_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO roles (id, name, description, created_at)
            SELECT gen_random_uuid(), v.name, v.description, now()
            FROM (VALUES
                ('training_coordinator', 'Bulk upload and stage updates'),
                ('trainer', 'Review trainee performance'),
                ('hr', 'Training outcomes and insights'),
                ('business_head', 'Dashboards and effectiveness'),
                ('system_admin', 'Users, config, audit')
            ) AS v(name, description)
            ON CONFLICT (name) DO NOTHING;
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO training_stage_types (id, code, label, sort_order, is_active)
            SELECT gen_random_uuid(), v.code, v.label, v.sort_order, true
            FROM (VALUES
                ('SPARK', 'Spark', 1),
                ('FOUNDATION', 'Foundation', 2),
                ('CODING_TEST', 'Coding Test', 3),
                ('PROJECT', 'Project', 4),
                ('COMPETENCY_TRAINING', 'Competency Training', 5)
            ) AS v(code, label, sort_order)
            ON CONFLICT (code) DO NOTHING;
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO streams (id, code, label, is_active, created_at)
            SELECT gen_random_uuid(), v.code, v.label, true, now()
            FROM (VALUES
                ('JAVA', 'Java'),
                ('PYTHON', 'Python'),
                ('DATA', 'Data'),
                ('QA', 'QA'),
                ('CLOUD', 'Cloud')
            ) AS v(code, label)
            ON CONFLICT (code) DO NOTHING;
            """
        )
    )

    # Assessment catalog: code, program, label, default_max_score, display_order
    op.execute(
        sa.text(
            """
            INSERT INTO assessment_catalog (id, code, program, label, default_max_score, display_order, is_active)
            SELECT gen_random_uuid(), v.code, v.program, v.label, v.mx::numeric, v.ord, true
            FROM (VALUES
                ('SPARK_P1_A1', 'SPARK', 'Spark Phase 1 – Attempt 1', 100, 1),
                ('SPARK_P1_A2', 'SPARK', 'Spark Phase 1 – Attempt 2', 100, 2),
                ('SPARK_FINAL', 'SPARK', 'Spark Final Score', 100, 3),
                ('FM1', 'FOUNDATION', 'Foundation Module 1', 100, 10),
                ('FM2', 'FOUNDATION', 'Foundation Module 2', 100, 11),
                ('FM3', 'FOUNDATION', 'Foundation Module 3', 100, 12),
                ('SQL', 'TECHNICAL', 'SQL', 100, 20),
                ('JAVA', 'TECHNICAL', 'Java', 100, 21),
                ('PYTHON', 'TECHNICAL', 'Python', 100, 22),
                ('PROJECT', 'PROJECT', 'Project score', 100, 30),
                ('PROJECT_MENTOR', 'PROJECT', 'Mentor evaluation', 100, 31),
                ('SA1', 'SOFT_SKILL', 'SA1', 100, 40),
                ('SA2', 'SOFT_SKILL', 'SA2', 100, 41),
                ('SA3', 'SOFT_SKILL', 'SA3', 100, 42),
                ('SA4', 'SOFT_SKILL', 'SA4', 100, 43),
                ('SA5', 'SOFT_SKILL', 'SA5', 100, 44),
                ('SA6', 'SOFT_SKILL', 'SA6', 100, 45),
                ('SP1', 'SOFT_SKILL', 'SP1', 100, 46),
                ('SP2', 'SOFT_SKILL', 'SP2', 100, 47),
                ('CT1', 'CODING_TEST', 'Coding Test 1', 100, 50),
                ('CT2', 'CODING_TEST', 'Coding Test 2', 100, 51),
                ('CT3', 'CODING_TEST', 'Coding Test 3', 100, 52),
                ('CT4', 'CODING_TEST', 'Coding Test 4', 100, 53),
                ('CT5', 'CODING_TEST', 'Coding Test 5', 100, 54),
                ('CT6', 'CODING_TEST', 'Coding Test 6', 100, 55),
                ('CT7', 'CODING_TEST', 'Coding Test 7', 100, 56)
            ) AS v(code, program, label, mx, ord)
            ON CONFLICT (code) DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM assessment_catalog WHERE code IN ("
            "'SPARK_P1_A1','SPARK_P1_A2','SPARK_FINAL','FM1','FM2','FM3','SQL','JAVA','PYTHON',"
            "'PROJECT','PROJECT_MENTOR','SA1','SA2','SA3','SA4','SA5','SA6','SP1','SP2',"
            "'CT1','CT2','CT3','CT4','CT5','CT6','CT7');"
        )
    )
    op.execute(sa.text("DELETE FROM streams WHERE code IN ('JAVA','PYTHON','DATA','QA','CLOUD');"))
    op.execute(
        sa.text(
            "DELETE FROM training_stage_types WHERE code IN "
            "('SPARK','FOUNDATION','CODING_TEST','PROJECT','COMPETENCY_TRAINING');"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM roles WHERE name IN "
            "('training_coordinator','trainer','hr','business_head','system_admin');"
        )
    )
