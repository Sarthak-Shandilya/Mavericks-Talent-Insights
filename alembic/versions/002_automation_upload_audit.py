"""Automation, classification, toppers, uploads, audit.

Revision ID: 002_automation_upload_audit
Revises: 001_core_schema
Create Date: 2026-02-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_automation_upload_audit"
down_revision: Union[str, Sequence[str], None] = "001_core_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scoring_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("weights", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("high_threshold", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("average_threshold", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX ix_scoring_configs_one_active ON scoring_configs ((1)) "
            "WHERE (is_active IS TRUE)"
        )
    )

    op.create_table(
        "topper_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("topper_type", sa.String(length=32), nullable=False),
        sa.Column("scope_field", sa.String(length=64), nullable=True),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("top_n", sa.Integer(), nullable=True),
        sa.Column("top_percent", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("min_score", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_topper_rules_topper_type"), "topper_rules", ["topper_type"], unique=False)

    op.create_table(
        "performance_classifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("composite_score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("scoring_config_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scoring_config_id"], ["scoring_configs.id"]),
        sa.ForeignKeyConstraint(["trainee_id"], ["trainees.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("trainee_id", name="uq_performance_classifications_trainee"),
    )
    op.create_index(
        op.f("ix_performance_classifications_trainee_id"),
        "performance_classifications",
        ["trainee_id"],
        unique=False,
    )

    op.create_table(
        "classification_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("override_classification", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["trainee_id"], ["trainees.id"], ondelete="CASCADE"),
    )
    op.create_index(
        op.f("ix_classification_overrides_trainee_id"),
        "classification_overrides",
        ["trainee_id"],
        unique=False,
    )

    op.create_table(
        "topper_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topper_type", sa.String(length=32), nullable=False),
        sa.Column("scope_value", sa.String(length=255), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rule_version", sa.Integer(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["topper_rules.id"]),
        sa.ForeignKeyConstraint(["trainee_id"], ["trainees.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_topper_flags_scope_value"), "topper_flags", ["scope_value"], unique=False)
    op.create_index(op.f("ix_topper_flags_topper_type"), "topper_flags", ["topper_type"], unique=False)
    op.create_index(op.f("ix_topper_flags_trainee_id"), "topper_flags", ["trainee_id"], unique=False)

    op.create_table(
        "upload_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("upload_type", sa.String(length=32), nullable=False),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("blob_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("success_count", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column("template_version", sa.String(length=32), nullable=True),
        sa.Column("error_report_url", sa.Text(), nullable=True),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_upload_batches_status"), "upload_batches", ["status"], unique=False)
    op.create_index(op.f("ix_upload_batches_upload_type"), "upload_batches", ["upload_type"], unique=False)
    op.create_index(
        op.f("ix_upload_batches_uploaded_by_user_id"),
        "upload_batches",
        ["uploaded_by_user_id"],
        unique=False,
    )

    op.create_table(
        "upload_row_errors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("column_name", sa.String(length=128), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["upload_id"], ["upload_batches.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_upload_row_errors_upload_id"), "upload_row_errors", ["upload_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("old_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_request_id"), "audit_logs", ["request_id"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("upload_row_errors")
    op.drop_table("upload_batches")
    op.drop_table("topper_flags")
    op.drop_table("classification_overrides")
    op.drop_table("performance_classifications")
    op.drop_table("topper_rules")
    op.execute(sa.text("DROP INDEX IF EXISTS ix_scoring_configs_one_active"))
    op.drop_table("scoring_configs")
