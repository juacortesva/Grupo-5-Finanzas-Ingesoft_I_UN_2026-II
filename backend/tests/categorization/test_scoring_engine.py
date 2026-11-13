from decimal import Decimal

import pytest

from src.categorization.engine import ScoringEngine
from src.categorization.enums import FinancialCategory
from src.categorization.schemas import ScoredAnswerDTO
from src.core.exceptions import InvalidInputError


def test_determine_category_when_on_threshold_then_assigns_lower_risk() -> None:
    # Arrange (BR-05: umbral exacto 50.00 entre CONSERVATIVE y MODERATE)
    engine = ScoringEngine(
        conservative_threshold=Decimal("50.00"),
        moderate_threshold=Decimal("80.00"),
    )

    # Act
    category_low = engine.determine_category(Decimal("50.00"))
    category_mid = engine.determine_category(Decimal("80.00"))
    category_high = engine.determine_category(Decimal("80.01"))

    # Assert
    assert category_low == FinancialCategory.CONSERVATIVE
    assert category_mid == FinancialCategory.MODERATE
    assert category_high == FinancialCategory.AGGRESSIVE


def test_calculate_score_when_valid_decimal_answers_then_returns_exact_sum() -> None:
    # Arrange
    engine = ScoringEngine()
    answers = [
        ScoredAnswerDTO(
            question_id=1,
            option_value=Decimal("20.00"),
            weight=Decimal("1.50"),
        ),
        ScoredAnswerDTO(
            question_id=2,
            option_value=Decimal("60.00"),
            weight=Decimal("0.50"),
        ),
    ]

    # Act
    score = engine.calculate_score(answers)

    # Assert
    assert score == Decimal("60.00")


def test_calculate_score_when_answers_empty_then_raises_invalid_input_error() -> None:
    # Arrange
    engine = ScoringEngine()

    # Act & Assert
    with pytest.raises(InvalidInputError):
        engine.calculate_score([])
