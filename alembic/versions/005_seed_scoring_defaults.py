"""Seed default scoring config and topper rules.

Revision ID: 005_seed_scoring_defaults
Revises: 004_upload_batch_file_hash
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_seed_scoring_defaults"
down_revision: Union[str, Sequence[str], None] = "004_upload_batch_file_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO scoring_configs (id, version, is_active, weights, high_threshold, average_threshold)
            SELECT gen_random_uuid(), 1, true,
                '{"SPARK":0.15,"FOUNDATION":0.25,"TECHNICAL":0.20,"PROJECT":0.15,"SOFT_SKILL":0.10,"CODING_TEST":0.15}'::jsonb,
                75, 50
            WHERE NOT EXISTS (SELECT 1 FROM scoring_configs WHERE is_active = true);
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO topper_rules (id, topper_type, scope_field, metric, top_n, top_percent, min_score, is_active, version)
            SELECT gen_random_uuid(), v.tt, v.scope, v.metric, v.top_n, NULL, v.min_score, true, 1
            FROM (VALUES
                ('SPARK', NULL::varchar, 'spark_score', 5, 70),
                ('FOUNDATION', NULL, 'foundation_score', 5, 70),
                ('STREAM', 'stream_code', 'composite_score', 3, 75),
                ('BATCH', 'batch_code', 'composite_score', 3, 75),
                ('COMPETENCY', 'assigned_competency', 'composite_score', 3, 75)
            ) AS v(tt, scope, metric, top_n, min_score)
            WHERE NOT EXISTS (
                SELECT 1 FROM topper_rules r WHERE r.topper_type = v.tt AND r.is_active = true
            );
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM topper_rules WHERE version = 1"))
    op.execute(sa.text("DELETE FROM scoring_configs WHERE version = 1"))
