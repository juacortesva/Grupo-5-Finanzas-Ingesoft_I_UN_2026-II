"""Creacion inicial de esquema REQ-01 (6 tablas incluyendo question_option).

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "client",
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("client_id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "question",
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column("weight", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("weight >= 0", name="ck_question_weight_non_negative"),
        sa.PrimaryKeyConstraint("question_id"),
    )

    op.create_table(
        "question_option",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint(
            "option_number > 0", name="ck_question_option_number_positive"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["question.question_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "question_id",
            "option_number",
            name="uq_question_option_question_number",
        ),
    )

    op.create_table(
        "survey",
        sa.Column("survey_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["client_id"], ["client.client_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("survey_id"),
    )
    op.create_index(
        "uq_survey_single_draft_per_client",
        "survey",
        ["client_id"],
        unique=True,
        postgresql_where=sa.text("status = 'DRAFT'"),
        sqlite_where=sa.text("status = 'DRAFT'"),
    )

    op.create_table(
        "answer",
        sa.Column("answer_id", sa.Uuid(), nullable=False),
        sa.Column("survey_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_option", sa.Integer(), nullable=False),
        sa.Column(
            "option_value", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.CheckConstraint(
            "selected_option > 0", name="ck_answer_selected_option_positive"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["question.question_id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["survey_id"], ["survey.survey_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("answer_id"),
        sa.UniqueConstraint(
            "survey_id", "question_id", name="uq_answer_survey_question"
        ),
    )

    op.create_table(
        "financial_profile",
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("survey_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_category", sa.String(length=32), nullable=False),
        sa.Column("evaluation_status", sa.String(length=16), nullable=False),
        sa.Column(
            "total_score", sa.Numeric(precision=10, scale=2), nullable=True
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(evaluation_status = 'ERROR' "
            "AND assigned_category = 'UNDER_EVALUATION' "
            "AND total_score IS NULL) "
            "OR "
            "(evaluation_status = 'COMPLETED' "
            "AND assigned_category IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE') "
            "AND total_score IS NOT NULL)",
            name="ck_financial_profile_br06_coherence",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["client.client_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["survey_id"], ["survey.survey_id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("profile_id"),
        sa.UniqueConstraint("client_id"),
    )


def downgrade() -> None:
    op.drop_table("financial_profile")
    op.drop_table("answer")
    op.drop_index("uq_survey_single_draft_per_client", table_name="survey")
    op.drop_table("survey")
    op.drop_table("question_option")
    op.drop_table("question")
    op.drop_table("client")
