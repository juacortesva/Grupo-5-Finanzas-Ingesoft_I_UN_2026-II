"""Dobles del Módulo Survey.

- `InMemorySurveyRepository` (fake): cumple el `Protocol` `SurveyRepository`
  (CT-04, CT-05, CT-07, CT-08) guardando las encuestas en un diccionario.
- `StubCategorizationService` (stub): reemplaza a `CategorizationService`
  (CT-10) y devuelve un resultado fijo.
- `StubSurveyManager` (stub): reemplaza a `SurveyManager` (CT-03, CT-09) para
  probar `SurveyRouter` sin base de datos.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.categorization.enums import EvaluationStatus, FinancialCategory
from src.categorization.schemas import EvaluationResult, ScoredAnswerDTO
from src.categorization.service import CategorizationService
from src.survey.enums import SurveyStatus
from src.survey.schemas import Answer, AnswerOption, Question, Survey
from src.survey.service import SurveyManager

OPTION_VALUES: tuple[Decimal, ...] = (Decimal("10.00"), Decimal("20.00"))
STUB_SCORE = Decimal("65.00")


def build_question(
    question_id: int, weight: Decimal = Decimal("1.00"), is_required: bool = True
) -> Question:
    """Construye una pregunta de catálogo con dos opciones (valores 10 y 20)."""
    options = [
        AnswerOption(
            id=question_id * 10 + number,
            question_id=question_id,
            option_number=number,
            text=f"Opción {number}",
            value=value,
        )
        for number, value in enumerate(OPTION_VALUES, start=1)
    ]
    return Question(
        question_id=question_id,
        text=f"Pregunta {question_id}",
        weight=weight,
        display_order=question_id,
        is_required=is_required,
        options=options,
    )


def build_catalog(size: int = 2) -> list[Question]:
    """Catálogo activo de `size` preguntas obligatorias (BR-01 exige 1..10)."""
    return [build_question(question_id) for question_id in range(1, size + 1)]


def build_survey(
    user_id: UUID,
    questions: list[Question],
    answers: list[Answer] | None = None,
    status: SurveyStatus = SurveyStatus.DRAFT,
) -> Survey:
    """Construye una entidad `Survey` lista para precargar en el fake."""
    return Survey(
        survey_id=uuid4(),
        user_id=user_id,
        status=status,
        started_at=datetime.now(UTC),
        completed_at=None,
        questions=questions,
        answers=answers or [],
    )


def build_result(
    survey_id: UUID, category: FinancialCategory = FinancialCategory.MODERATE
) -> EvaluationResult:
    """`EvaluationResult` coherente con BR-06 para la categoría indicada."""
    is_provisional = category == FinancialCategory.UNDER_EVALUATION
    return EvaluationResult(
        survey_id=survey_id,
        assigned_category=category,
        evaluation_status=(
            EvaluationStatus.ERROR if is_provisional else EvaluationStatus.COMPLETED
        ),
        total_score=None if is_provisional else STUB_SCORE,
    )


class InMemorySurveyRepository:
    """Fake de `SurveyRepository` que simula BR-02, BR-03 y el aislamiento 404."""

    def __init__(self, questions: list[Question]) -> None:
        self.questions = questions
        self.surveys: dict[UUID, Survey] = {}
        self.save_calls = 0
        # Interruptores para simular escenarios de los contratos.
        self.fail_on_save = False
        self.simulate_concurrent_close = False

    def add(self, survey: Survey) -> Survey:
        """Precarga una encuesta existente (Arrange de las pruebas)."""
        self.surveys[survey.survey_id] = survey
        return survey

    def list_active_questions(self) -> list[Question]:
        return list(self.questions)

    def find_draft_by_user_id(self, user_id: UUID) -> Survey | None:
        return next(
            (
                s
                for s in self.surveys.values()
                if s.user_id == user_id and s.status == SurveyStatus.DRAFT
            ),
            None,
        )

    def find_by_id(self, survey_id: UUID, user_id: UUID) -> Survey | None:
        survey = self.surveys.get(survey_id)
        if survey is None or survey.user_id != user_id:
            return None  # Inexistente y ajena son indistinguibles (ADR-0006).
        return survey

    def save(self, survey: Survey) -> Survey | None:
        self.save_calls += 1
        if self.fail_on_save:
            raise RuntimeError("Falla simulada de persistencia")
        if survey.status == SurveyStatus.DRAFT:
            return self._save_draft(survey)
        return self._close(survey)

    def update_status(
        self,
        survey_id: UUID,
        user_id: UUID,
        new_status: SurveyStatus,
        completed_at: datetime | None = None,
    ) -> Survey | None:
        current = self.find_by_id(survey_id, user_id)
        if current is None:
            return None
        updates = {"status": new_status, "completed_at": completed_at}
        return self._close(current.model_copy(update=updates))

    def save_answer(self, survey_id: UUID, user_id: UUID, answer: Answer) -> bool:
        survey = self.find_by_id(survey_id, user_id)
        if survey is None or survey.status != SurveyStatus.DRAFT:
            return False
        if self.simulate_concurrent_close:
            return False  # Otro request cerró la encuesta antes del lock (CT-08).
        kept = [a for a in survey.answers if a.question_id != answer.question_id]
        self.surveys[survey_id] = survey.model_copy(update={"answers": [*kept, answer]})
        return True

    def _save_draft(self, survey: Survey) -> Survey:
        winner = self.find_draft_by_user_id(survey.user_id)
        if winner is not None:
            return winner  # CT-05 caso A: gana el borrador ya existente.
        self.surveys[survey.survey_id] = survey
        return survey

    def _close(self, survey: Survey) -> Survey | None:
        stored = self.surveys.get(survey.survey_id)
        if self.simulate_concurrent_close or stored is None:
            return None
        if stored.status != SurveyStatus.DRAFT:
            return None  # UPDATE ... WHERE status = 'DRAFT' no afecta filas.
        self.surveys[survey.survey_id] = survey
        return survey


class StubCategorizationService(CategorizationService):
    """Stub de `CategorizationService`: respuesta fija y registro de llamadas."""

    def __init__(
        self, result_category: FinancialCategory = FinancialCategory.MODERATE
    ) -> None:
        # No llama a super(): el stub no necesita motor ni repositorio reales.
        self._result_category = result_category
        self.calls: list[tuple[UUID, UUID, list[ScoredAnswerDTO]]] = []

    def evaluate_profile(
        self,
        user_id: UUID,
        survey_id: UUID,
        answers: list[ScoredAnswerDTO],
    ) -> EvaluationResult:
        self.calls.append((user_id, survey_id, answers))
        return build_result(survey_id, self._result_category)


class StubSurveyManager(SurveyManager):
    """Stub de `SurveyManager` para probar `SurveyRouter` sin base de datos.

    Devuelve un borrador fijo en `start_survey` y un `EvaluationResult` fijo en
    `complete_survey`. Si se configura `error`, todas las operaciones lo lanzan
    (útil para verificar la traducción a 404, 409, 422 o 503 en el router).
    """

    def __init__(
        self,
        draft: Survey | None = None,
        result_category: FinancialCategory = FinancialCategory.MODERATE,
        error: Exception | None = None,
    ) -> None:
        # No llama a super(): el stub no necesita repositorio ni categorización.
        self.draft = draft or build_survey(uuid4(), build_catalog())
        self.result_category = result_category
        self.error = error
        self.calls: list[str] = []

    def start_survey(self, user_id: UUID) -> Survey:
        self._register("start_survey")
        return self.draft.model_copy(update={"user_id": user_id})

    def complete_survey(self, survey_id: UUID, user_id: UUID) -> EvaluationResult:
        self._register("complete_survey")
        return build_result(survey_id, self.result_category)

    def _register(self, operation: str) -> None:
        self.calls.append(operation)
        if self.error is not None:
            raise self.error
