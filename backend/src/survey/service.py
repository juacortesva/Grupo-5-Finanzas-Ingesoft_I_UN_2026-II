from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.categorization.schemas import EvaluationResult, ScoredAnswerDTO
from src.categorization.service import CategorizationService
from src.core.exceptions import InvalidStateError, NotFoundError, ValidationError
from src.survey.enums import SurveyStatus
from src.survey.repository import SurveyRepository
from src.survey.schemas import Answer, Question, SaveAnswerRequest, Survey


class SurveyManager:
    """Coordina el ciclo de vida DRAFT/COMPLETED de la encuesta (CT-03, 06, 09)."""

    def __init__(
        self,
        survey_repo: SurveyRepository,
        categorization_service: CategorizationService,
    ) -> None:
        self._survey_repo = survey_repo
        self._categorization_service = categorization_service

    def start_survey(self, user_id: UUID) -> Survey:
        """Inicia o recupera el único borrador DRAFT del cliente (BR-01, BR-02)."""
        questions = self._survey_repo.list_active_questions()
        if not 1 <= len(questions) <= 10:
            raise RuntimeError("Catálogo de preguntas inválido para BR-01")

        existing = self._survey_repo.find_draft_by_user_id(user_id)
        if existing is not None:
            return existing

        new_survey = Survey(
            survey_id=uuid4(),
            user_id=user_id,
            status=SurveyStatus.DRAFT,
            started_at=datetime.now(UTC),
            completed_at=None,
            questions=questions,
            answers=[],
        )
        persisted = self._survey_repo.save(new_survey)
        if persisted is None:
            raise RuntimeError("No fue posible crear el borrador de encuesta")
        return persisted

    def resume_survey(self, user_id: UUID) -> Survey | None:
        """Recupera el borrador DRAFT activo del cliente si existe (BR-02)."""
        return self._survey_repo.find_draft_by_user_id(user_id)

    def save_answer(
        self, survey_id: UUID, user_id: UUID, payload: SaveAnswerRequest
    ) -> None:
        """Valida propiedad, estado DRAFT y opción en question_option (CT-06)."""
        survey = self._survey_repo.find_by_id(survey_id, user_id)
        if survey is None:
            raise NotFoundError("Encuesta no encontrada")
        if survey.status != SurveyStatus.DRAFT:
            raise InvalidStateError(
                "La encuesta ya fue completada y no admite modificaciones"
            )

        option_value = self._resolve_option_value(
            survey.questions, payload.question_id, payload.selected_option
        )
        answer = Answer(
            question_id=payload.question_id,
            selected_option=payload.selected_option,
            option_value=option_value,
        )
        applied = self._survey_repo.save_answer(survey_id, user_id, answer)
        if not applied:
            raise InvalidStateError(
                "La encuesta ya fue completada y no admite modificaciones"
            )

    def complete_survey(self, survey_id: UUID, user_id: UUID) -> EvaluationResult:
        """Cierra la encuesta a COMPLETED (BR-03) y evalúa perfil (CT-09)."""
        survey = self._survey_repo.find_by_id(survey_id, user_id)
        if survey is None:
            raise NotFoundError("Encuesta no encontrada")
        if survey.status != SurveyStatus.DRAFT:
            raise InvalidStateError("La encuesta ya fue completada")

        self._ensure_required_answered(survey)
        closing_survey = survey.model_copy(
            update={
                "status": SurveyStatus.COMPLETED,
                "completed_at": datetime.now(UTC),
            }
        )
        closed = self._survey_repo.save(closing_survey)
        if closed is None:
            raise InvalidStateError("La encuesta ya fue completada")

        scored_answers = self._build_scored_answers(closed)
        return self._categorization_service.evaluate_profile(
            user_id, survey_id, scored_answers
        )

    def _resolve_option_value(
        self, questions: list[Question], question_id: int, selected_option: int
    ) -> Decimal:
        question = next(
            (q for q in questions if q.question_id == question_id), None
        )
        if question is None:
            raise ValidationError("Pregunta inexistente o inactiva")

        option = next(
            (o for o in question.options if o.option_number == selected_option), None
        )
        if option is None:
            raise ValidationError("Opción inválida para la pregunta seleccionada")
        return option.value

    def _ensure_required_answered(self, survey: Survey) -> None:
        answered_ids = {ans.question_id for ans in survey.answers}
        missing = [
            q.question_id
            for q in survey.questions
            if q.is_required and q.question_id not in answered_ids
        ]
        if missing:
            raise ValidationError("Faltan preguntas obligatorias por responder")

    def _build_scored_answers(self, survey: Survey) -> list[ScoredAnswerDTO]:
        weights = {q.question_id: q.weight for q in survey.questions}
        return [
            ScoredAnswerDTO(
                question_id=ans.question_id,
                option_value=ans.option_value,
                weight=weights[ans.question_id],
            )
            for ans in survey.answers
            if ans.question_id in weights
        ]
