"""add design constraints for req_01

Alinea el esquema con `02_Interaction_and_Data_Design.md` §2.2 y §2.5:
CHECKs de valores permitidos y coherencia, índice único de `display_order`
en el catálogo activo, BR-02 (máx. 10 preguntas activas) y `completed_at`
inmutable una vez fijado.

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

# BR-02 (REQ-01): a lo sumo 10 filas activas en `question` (diseño 02 §2.5).
BR02_FUNCTION = """
CREATE FUNCTION enforce_max_active_questions() RETURNS trigger AS $$
BEGIN
    IF (SELECT count(*) FROM question WHERE is_active) > 10 THEN
        RAISE EXCEPTION 'BR-02: maximo 10 preguntas activas'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""
BR02_TRIGGER = """
CREATE CONSTRAINT TRIGGER trg_question_max_active
AFTER INSERT OR UPDATE OF is_active ON question
DEFERRABLE INITIALLY IMMEDIATE
FOR EACH ROW EXECUTE FUNCTION enforce_max_active_questions();
"""

# Diseño 02 §2.5: una encuesta COMPLETED no vuelve a DRAFT; completed_at es
# inmutable una vez fijado (el CHECK ata status y completed_at).
COMPLETED_AT_FUNCTION = """
CREATE FUNCTION enforce_completed_at_immutable() RETURNS trigger AS $$
BEGIN
    IF OLD.completed_at IS NOT NULL
       AND NEW.completed_at IS DISTINCT FROM OLD.completed_at THEN
        RAISE EXCEPTION 'completed_at es inmutable en una encuesta COMPLETED'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
COMPLETED_AT_TRIGGER = """
CREATE TRIGGER trg_survey_completed_at_immutable
BEFORE UPDATE ON survey
FOR EACH ROW EXECUTE FUNCTION enforce_completed_at_immutable();
"""


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
    for statement in (
        BR02_FUNCTION,
        BR02_TRIGGER,
        COMPLETED_AT_FUNCTION,
        COMPLETED_AT_TRIGGER,
    ):
        op.execute(statement)


def downgrade() -> None:
    """Revierte las restricciones agregadas en upgrade()."""
    op.execute("DROP TRIGGER trg_survey_completed_at_immutable ON survey")
    op.execute("DROP FUNCTION enforce_completed_at_immutable()")
    op.execute("DROP TRIGGER trg_question_max_active ON question")
    op.execute("DROP FUNCTION enforce_max_active_questions()")
    op.drop_index("ix_question_active_display_order", table_name="question")
    for name, table, _ in reversed(CHECKS):
        op.drop_constraint(name, table, type_="check")
