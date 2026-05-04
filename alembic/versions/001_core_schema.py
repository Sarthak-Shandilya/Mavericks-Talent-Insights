"""Core schema: auth, reference data shells, batches, trainees, stages, assessments, competencies.

Revision ID: 001_core_schema
Revises:
Create Date: 2026-02-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_core_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_table(
        "streams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("code", name="uq_streams_code"),
    )
    op.create_table(
        "training_stage_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("code", name="uq_training_stage_types_code"),
    )
    op.create_table(
        "assessment_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("program", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("default_max_score", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("code", name="uq_assessment_catalog_code"),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("stream_hint", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("code", name="uq_batches_code"),
    )

    op.create_table(
        "trainees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", sa.String(length=64), nullable=False),
        sa.Column("superset_id", sa.String(length=64), nullable=False),
        sa.Column("doj", sa.Date(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("gender", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("college_name", sa.String(length=512), nullable=False),
        sa.Column("college_city", sa.String(length=255), nullable=False),
        sa.Column("college_state", sa.String(length=255), nullable=False),
        sa.Column("base_location", sa.String(length=255), nullable=False),
        sa.Column("current_training_location", sa.String(length=255), nullable=False),
        sa.Column("training_status", sa.String(length=32), nullable=False),
        sa.Column("stream_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("current_training_stage_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("assigned_competency", sa.String(length=255), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"]),
        sa.ForeignKeyConstraint(["current_training_stage_id"], ["training_stage_types.id"]),
        sa.ForeignKeyConstraint(["stream_id"], ["streams.id"]),
        sa.UniqueConstraint("employee_id", name="uq_trainees_employee_id"),
    )
    op.create_index(op.f("ix_trainees_base_location"), "trainees", ["base_location"], unique=False)
    op.create_index(op.f("ix_trainees_current_training_location"), "trainees", ["current_training_location"], unique=False)
    op.create_index(op.f("ix_trainees_email"), "trainees", ["email"], unique=False)
    op.create_index(op.f("ix_trainees_employee_id"), "trainees", ["employee_id"], unique=False)
    op.create_index(op.f("ix_trainees_training_status"), "trainees", ["training_status"], unique=False)

    op.create_table(
        "training_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["stage_type_id"], ["training_stage_types.id"]),
        sa.ForeignKeyConstraint(["trainee_id"], ["trainees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("trainee_id", "stage_type_id", name="uq_training_stages_trainee_stage"),
    )
    op.create_index(op.f("ix_training_stages_trainee_id"), "training_stages", ["trainee_id"], unique=False)

    op.create_table(
        "assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("program", sa.String(length=32), nullable=False),
        sa.Column("assessment_code", sa.String(length=64), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("max_score", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("assessment_date", sa.Date(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("score <= max_score", name="ck_assessments_score_le_max"),
        sa.ForeignKeyConstraint(["trainee_id"], ["trainees.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("trainee_id", "assessment_code", "attempt_no", name="uq_assessments_trainee_code_attempt"),
    )
    op.create_index(op.f("ix_assessments_assessment_code"), "assessments", ["assessment_code"], unique=False)
    op.create_index(op.f("ix_assessments_program"), "assessments", ["program"], unique=False)
    op.create_index(op.f("ix_assessments_trainee_id"), "assessments", ["trainee_id"], unique=False)

    op.create_table(
        "trainee_competencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("competency_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("skill_level", sa.String(length=32), nullable=False),
        sa.Column("readiness_flag", sa.Boolean(), nullable=False),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["trainee_id"], ["trainees.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("trainee_id", "competency_name", name="uq_trainee_competency_name"),
    )
    op.create_index(op.f("ix_trainee_competencies_trainee_id"), "trainee_competencies", ["trainee_id"], unique=False)


def downgrade() -> None:
    op.drop_table("trainee_competencies")
    op.drop_table("assessments")
    op.drop_table("training_stages")
    op.drop_table("trainees")
    op.drop_table("batches")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("assessment_catalog")
    op.drop_table("training_stage_types")
    op.drop_table("streams")
    op.drop_table("roles")
