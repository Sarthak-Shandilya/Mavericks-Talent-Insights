"""Add file_hash for upload idempotency.

Revision ID: 004_upload_batch_file_hash
Revises: 003_seed_reference_data
Create Date: 2026-05-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_upload_batch_file_hash"
down_revision: Union[str, Sequence[str], None] = "003_seed_reference_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("upload_batches", sa.Column("file_hash", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_upload_batches_file_hash"), "upload_batches", ["file_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_upload_batches_file_hash"), table_name="upload_batches")
    op.drop_column("upload_batches", "file_hash")
