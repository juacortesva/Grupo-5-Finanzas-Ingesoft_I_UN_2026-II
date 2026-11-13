from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src.survey.enums import SurveyStatus
from src.survey.models import AnswerModel, QuestionModel, SurveyModel
from src.survey.schemas import Answer, AnswerOption, Question, Survey


class SurveyRepository(Protocol):
    """Contrato de acceso a datos del Módulo Survey (CT-04, CT-05, CT-07, CT-08)."""

    def list_active_questions(self) -> list[Question]:
        """Retorna el catálogo activo ordenado por display_order."""

    def find_draft_by_user_id(self, user_id: UUID) -> Survey | None:
        """Retorna el borrador DRAFT único del cliente o None (CT-04)."""

    def find_by_id(self, survey_id: UUID, user_id: UUID) -> Survey | None:
        """Retorna la encuesta si existe y pertenece a user_id (CT-07)."""

    def save(self, survey: Survey) -> Survey | None:
        """Crea DRAFT o ejecuta transición condicional a COMPLETED (CT-05)."""

    def save_answer(self, survey_id: UUID, user_id: UUID, answer: Answer) -> bool:
        """Persiste o actualiza una respuesta bajo bloqueo FOR UPDATE (CT-08)."""


class SqlAlchemySurveyRepository:
    """Implementación SQLAlchemy del repositorio de encuestas."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_active_questions(self) -> list[Question]:
        """Carga las preguntas activas con sus opciones ordenadas."""
        stmt = (
            select(QuestionModel)
            .where(QuestionModel.is_active.is_(True))
            .options(selectinload(QuestionModel.options))
            .order_by(QuestionModel.display_order)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_question(row) for row in rows]

    def find_draft_by_user_id(self, user_id: UUID) -> Survey | None:
        """Busca el único DRAFT activo del cliente (BR-02)."""
        stmt = (
            select(SurveyModel)
            .where(
                SurveyModel.client_id == user_id,
                SurveyModel.status == SurveyStatus.DRAFT.value,
            )
            .options(selectinload(SurveyModel.answers))
        )
        row = self._db.execute(stmt).scalar_one_or_none()
        if row is None:
            return None
        return self._to_survey(row, self.list_active_questions())

    def find_by_id(self, survey_id: UUID, user_id: UUID) -> Survey | None:
        """Recupera encuesta filtrando estrictamente por client_id (CT-07)."""
        stmt = (
            select(SurveyModel)
            .where(
                SurveyModel.survey_id == survey_id,
                SurveyModel.client_id == user_id,
            )
            .options(selectinload(SurveyModel.answers))
        )
        row = self._db.execute(stmt).scalar_one_or_none()
        if row is None:
            return None
        return self._to_survey(row, self.list_active_questions())

    def save(self, survey: Survey) -> Survey | None:
        """Crea DRAFT (caso A) o cierra a COMPLETED atómicamente (caso B)."""
        if survey.status == SurveyStatus.DRAFT:
            return self._create_draft(survey)
        return self._complete_transition(survey)

    def _create_draft(self, survey: Survey) -> Survey:
        """Inserta nuevo borrador o devuelve el existente ante carrera BR-02."""
        record = SurveyModel(
            survey_id=survey.survey_id,
            client_id=survey.user_id,
            status=SurveyStatus.DRAFT.value,
            started_at=survey.started_at,
            completed_at=None,
            updated_at=survey.started_at,
        )
        try:
            self._db.add(record)
            self._db.commit()
            self._db.refresh(record)
        except IntegrityError:
            self._db.rollback()
            existing = self.find_draft_by_user_id(survey.user_id)
            if existing is not None:
                return existing
            raise
        return self._to_survey(record, survey.questions)

    def _complete_transition(self, survey: Survey) -> Survey | None:
        """Transición condicional DRAFT -> COMPLETED (CT-05, caso B)."""
        now = survey.completed_at or datetime.now(UTC)
        stmt = (
            update(SurveyModel)
            .where(
                SurveyModel.survey_id == survey.survey_id,
                SurveyModel.client_id == survey.user_id,
                SurveyModel.status == SurveyStatus.DRAFT.value,
            )
            .values(
                status=SurveyStatus.COMPLETED.value,
                completed_at=now,
                updated_at=now,
            )
            .returning(SurveyModel.survey_id)
        )
        updated_id = self._db.execute(stmt).scalar_one_or_none()
        if updated_id is None:
            self._db.rollback()
            return None
        self._db.commit()
        return self.find_by_id(survey.survey_id, survey.user_id)

    def save_answer(self, survey_id: UUID, user_id: UUID, answer: Answer) -> bool:
        """Bloquea encuesta DRAFT y realiza upsert de respuesta (CT-08)."""
        stmt = (
            select(SurveyModel)
            .where(
                SurveyModel.survey_id == survey_id,
                SurveyModel.client_id == user_id,
                SurveyModel.status == SurveyStatus.DRAFT.value,
            )
            .with_for_update()
        )
        survey_row = self._db.execute(stmt).scalar_one_or_none()
        if survey_row is None:
            self._db.rollback()
            return False

        self._upsert_answer(survey_id, answer)
        survey_row.updated_at = datetime.now(UTC)
        self._db.commit()
        return True

    def _upsert_answer(self, survey_id: UUID, answer: Answer) -> None:
        """Inserta o actualiza la respuesta para (survey_id, question_id)."""
        existing = self._db.execute(
            select(AnswerModel).where(
                AnswerModel.survey_id == survey_id,
                AnswerModel.question_id == answer.question_id,
            )
        ).scalar_one_or_none()

        if existing is None:
            self._db.add(
                AnswerModel(
                    survey_id=survey_id,
                    question_id=answer.question_id,
                    selected_option=answer.selected_option,
                    option_value=answer.option_value,
                )
            )
            return

        existing.selected_option = answer.selected_option
        existing.option_value = answer.option_value

    def _to_question(self, row: QuestionModel) -> Question:
        return Question(
            question_id=row.question_id,
            text=row.text,
            weight=row.weight,
            display_order=row.display_order,
            is_required=row.is_required,
            options=[
                AnswerOption(
                    id=opt.id,
                    question_id=opt.question_id,
                    option_number=opt.option_number,
                    text=opt.text,
                    value=opt.value,
                )
                for opt in row.options
            ],
        )

    def _to_survey(self, row: SurveyModel, questions: list[Question]) -> Survey:
        return Survey(
            survey_id=row.survey_id,
            user_id=row.client_id,
            status=SurveyStatus(row.status),
            started_at=row.started_at,
            completed_at=row.completed_at,
            questions=questions,
            answers=[
                Answer(
                    question_id=ans.question_id,
                    selected_option=ans.selected_option,
                    option_value=ans.option_value,
                )
                for ans in row.answers
            ],
        )
