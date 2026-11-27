"""Pruebas unitarias de `CategorizationService` con dobles en memoria (CT-10).

Cubren el camino feliz y la validación defensiva de CT-10 sin base de datos.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.categorization.engine import ScoringEngine
from src.categorization.enums import EvaluationStatus, FinancialCategory
from src.categorization.schemas import ScoredAnswerDTO
from src.categorization.service import CategorizationService
from src.core.exceptions import InvalidInputError
from tests.doubles.categorization_doubles import InMemoryProfileRepository

USER_ID = uuid4()
SURVEY_ID = uuid4()
ANSWERS = [
    ScoredAnswerDTO(question_id=1, option_value=Decimal("30.00"), weight=Decimal("1")),
    ScoredAnswerDTO(question_id=2, option_value=Decimal("35.00"), weight=Decimal("1")),
]


def test_evaluate_profile_when_valid_answers_then_saves_definitive_category() -> None:
    # Arrange
    repo = InMemoryProfileRepository()
    service = CategorizationService(ScoringEngine(), repo)

    # Act
    result = service.evaluate_profile(USER_ID, SURVEY_ID, ANSWERS)

    # Assert (65.00 con umbrales provisionales 50/80 -> MODERATE)
    assert result.assigned_category == FinancialCategory.MODERATE
    assert result.evaluation_status == EvaluationStatus.COMPLETED
    assert result.total_score == Decimal("65.00")
    profile = repo.find_by_user_id(USER_ID)
    assert profile is not None
    assert profile.survey_id == SURVEY_ID
    assert profile.total_score == Decimal("65.00")


def test_evaluate_profile_when_answers_empty_then_raises_without_saving() -> None:
    # Arrange
    repo = InMemoryProfileRepository()
    service = CategorizationService(ScoringEngine(), repo)

    # Act & Assert
    with pytest.raises(InvalidInputError):
        service.evaluate_profile(USER_ID, SURVEY_ID, [])
    assert repo.received == []
