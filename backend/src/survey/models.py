from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.survey.enums import SurveyStatus


class SurveyModel(Base):
    """Ejecución del cuestionario de onboarding del cliente (REQ-01)."""

    __tablename__ = "survey"
    __table_args__ = (
        # Invariante REQ-01 Escenario 2: Máximo un borrador activo por cliente.
        Index(
            "ix_survey_one_draft_per_client",
            "client_id",
            unique=True,
            postgresql_where=text("status = 'DRAFT'"),
        ),
        # Diseño 02 §2.2: SURVEY.status no contiene ERROR.
        CheckConstraint(
            "status IN ('DRAFT', 'COMPLETED')", name="ck_survey_status_valid"
        ),
        # Diseño 02 §2.2: completed_at solo si status = COMPLETED.
        CheckConstraint(
            "(status = 'DRAFT' AND completed_at IS NULL)"
            " OR (status = 'COMPLETED' AND completed_at IS NOT NULL)",
            name="ck_survey_completed_at_consistent",
        ),
    )

    survey_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("client.client_id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=SurveyStatus.DRAFT.value, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class QuestionModel(Base):
    """Catálogo de preguntas parametrizadas de la encuesta (BR-02: máx. 10 activas)."""

    __tablename__ = "question"
    __table_args__ = (
        CheckConstraint("weight >= 0", name="ck_question_weight_non_negative"),
        # Diseño 02 §2.2: display_order único dentro del catálogo activo.
        Index(
            "ix_question_active_display_order",
            "display_order",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    question_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 4, asdecimal=True), nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AnswerModel(Base):
    """Respuesta individual persistida progresivamente por el cliente."""

    __tablename__ = "answer"
    __table_args__ = (
        UniqueConstraint("survey_id", "question_id", name="uq_answer_survey_question"),
        CheckConstraint(
            "selected_option > 0", name="ck_answer_selected_option_positive"
        ),
    )

    answer_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    survey_id: Mapped[UUID] = mapped_column(
        ForeignKey("survey.survey_id"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.question_id"), nullable=False
    )
    selected_option: Mapped[int] = mapped_column(Integer, nullable=False)
    option_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 4, asdecimal=True), nullable=False
    )
