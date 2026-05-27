"""Add percentage_completed for real-time upload progress.

Revision ID: 006_upload_percentage_completed
Revises: 005_seed_scoring_defaults
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_upload_percentage_completed"
down_revision: Union[str, Sequence[str], None] = "005_seed_scoring_defaults"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "upload_batches",
        sa.Column("percentage_completed", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("upload_batches", "percentage_completed")
