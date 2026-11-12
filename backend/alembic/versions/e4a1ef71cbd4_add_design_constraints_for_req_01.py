"""add design constraints for req_01

Alinea el esquema con `02_Interaction_and_Data_Design.md` §2.2 y §2.5.

Revision ID: e4a1ef71cbd4
Revises: 8cedce29f65b
Create Date: 2026-11-12 16:04:26.735224

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4a1ef71cbd4"
down_revision: str | Sequence[str] | None = "8cedce29f65b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CHECKS: list[tuple[str, str, str]] = [
    (
        "ck_survey_status_valid",
        "survey",
        "status IN ('DRAFT', 'COMPLETED')",
    ),
    (
        "ck_survey_completed_at_consistent",
        "survey",
        "(status = 'DRAFT' AND completed_at IS NULL)"
        " OR (status = 'COMPLETED' AND completed_at IS NOT NULL)",
    ),
    ("ck_question_weight_non_negative", "question", "weight >= 0"),
    ("ck_answer_selected_option_positive", "answer", "selected_option > 0"),
    (
        "ck_financial_profile_category_valid",
        "financial_profile",
        "assigned_category IN "
        "('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE', 'UNDER_EVALUATION')",
    ),
    (
        "ck_financial_profile_status_valid",
        "financial_profile",
        "evaluation_status IN ('COMPLETED', 'ERROR')",
    ),
    (
        "ck_financial_profile_error_is_provisional",
        "financial_profile",
        "evaluation_status <> 'ERROR' OR "
        "(assigned_category = 'UNDER_EVALUATION' AND total_score IS NULL)",
    ),
]


def upgrade() -> None:
    """Agrega CHECKs e índice único parcial de display_order."""
    for name, table, condition in CHECKS:
        op.create_check_constraint(name, table, condition)
    op.create_index(
        "ix_question_active_display_order",
        "question",
        ["display_order"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    """Revierte las restricciones agregadas en upgrade()."""
    op.drop_index("ix_question_active_display_order", table_name="question")
    for name, table, _ in reversed(CHECKS):
        op.drop_constraint(name, table, type_="check")
