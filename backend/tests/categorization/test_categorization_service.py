from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from src.categorization.engine import ScoringEngine
from src.categorization.enums import EvaluationStatus, FinancialCategory
from src.categorization.repository import SqlAlchemyProfileRepository
from src.categorization.schemas import ProfileEvaluation, ScoredAnswerDTO
from src.categorization.service import CategorizationService
from src.core.config import settings
from src.core.exceptions import EvaluationPersistenceError
from src.survey.enums import SurveyStatus
from src.survey.models import SurveyModel


class _FailingScoringEngine(ScoringEngine):
    """Motor simulado que lanza error técnico para probar BR-06."""

    def calculate_score(self, answers: list[ScoredAnswerDTO]) -> Decimal:
        raise RuntimeError("Falla simulada en motor de puntaje")


class _FailingProfileRepository(SqlAlchemyProfileRepository):
    """Repositorio simulado que falla también en el guardado provisional."""

    def save_category(self, user_id: UUID, evaluation: ProfileEvaluation):  # type: ignore[override]
        raise RuntimeError("Falla simulada de persistencia doble")


def _create_closed_survey(db_session: Session, user_id: UUID) -> UUID:
    survey_row = SurveyModel(
        client_id=user_id,
        status=SurveyStatus.COMPLETED.value,
    )
    db_session.add(survey_row)
    db_session.commit()
    db_session.refresh(survey_row)
    return survey_row.survey_id


def test_evaluate_profile_when_engine_fails_then_saves_under_evaluation_br06(
    db_session: Session,
) -> None:
    # Arrange
    user_id = UUID(settings.dev_user_1_id)
    survey_id = _create_closed_survey(db_session, user_id)
    repo = SqlAlchemyProfileRepository(db_session)
    service = CategorizationService(_FailingScoringEngine(), repo)
    answers = [
        ScoredAnswerDTO(
            question_id=1,
            option_value=Decimal("55.00"),
            weight=Decimal("1.00"),
        )
    ]

    # Act
    result = service.evaluate_profile(user_id, survey_id, answers)
    persisted = repo.find_by_user_id(user_id)

    # Assert (BR-06: categoría provisional UNDER_EVALUATION y puntaje nulo)
    assert result.assigned_category == FinancialCategory.UNDER_EVALUATION
    assert result.evaluation_status == EvaluationStatus.ERROR
    assert result.total_score is None
    assert persisted is not None
    assert persisted.assigned_category == FinancialCategory.UNDER_EVALUATION
    assert persisted.total_score is None


def test_evaluate_profile_when_double_failure_then_raises_persistence_error(
    db_session: Session,
) -> None:
    # Arrange
    user_id = UUID(settings.dev_user_1_id)
    survey_id = _create_closed_survey(db_session, user_id)
    service = CategorizationService(
        _FailingScoringEngine(),
        _FailingProfileRepository(db_session),
    )
    answers = [
        ScoredAnswerDTO(
            question_id=1,
            option_value=Decimal("55.00"),
            weight=Decimal("1.00"),
        )
    ]

    # Act & Assert
    with pytest.raises(EvaluationPersistenceError):
        service.evaluate_profile(user_id, survey_id, answers)
