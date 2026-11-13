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
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class SurveyModel(Base):
    """Modelo SQLAlchemy de la tabla survey (BR-02, BR-03)."""

    __tablename__ = "survey"
    __table_args__ = (
        Index(
            "uq_survey_single_draft_per_client",
            "client_id",
            unique=True,
            postgresql_where=text("status = 'DRAFT'"),
            sqlite_where=text("status = 'DRAFT'"),
        ),
    )

    survey_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    client_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("client.client_id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    answers: Mapped[list["AnswerModel"]] = relationship(
        back_populates="survey", cascade="all, delete-orphan"
    )


class QuestionModel(Base):
    """Modelo SQLAlchemy de la tabla question (BR-01)."""

    __tablename__ = "question"
    __table_args__ = (
        CheckConstraint("weight >= 0", name="ck_question_weight_non_negative"),
    )

    question_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    options: Mapped[list["QuestionOptionModel"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOptionModel.option_number",
    )


class QuestionOptionModel(Base):
    """Modelo SQLAlchemy del catálogo de opciones por pregunta."""

    __tablename__ = "question_option"
    __table_args__ = (
        UniqueConstraint(
            "question_id",
            "option_number",
            name="uq_question_option_question_number",
        ),
        CheckConstraint("option_number > 0", name="ck_question_option_number_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("question.question_id", ondelete="CASCADE"),
        nullable=False,
    )
    option_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=False
    )

    question: Mapped[QuestionModel] = relationship(back_populates="options")


class AnswerModel(Base):
    """Modelo SQLAlchemy de la tabla answer."""

    __tablename__ = "answer"
    __table_args__ = (
        UniqueConstraint("survey_id", "question_id", name="uq_answer_survey_question"),
        CheckConstraint(
            "selected_option > 0", name="ck_answer_selected_option_positive"
        ),
    )

    answer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    survey_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("survey.survey_id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("question.question_id", ondelete="RESTRICT"),
        nullable=False,
    )
    selected_option: Mapped[int] = mapped_column(Integer, nullable=False)
    option_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=False
    )

    survey: Mapped[SurveyModel] = relationship(back_populates="answers")
