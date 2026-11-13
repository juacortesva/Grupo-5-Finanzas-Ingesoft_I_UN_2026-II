from decimal import Decimal

from src.categorization.engine import ScoringEngine
from src.categorization.enums import FinancialCategory
from src.categorization.schemas import ScoredAnswerDTO


def test_determine_category_when_score_is_on_exact_threshold_then_assigns_lower_risk() -> None:  # noqa: E501
    # Arrange (BR-05: umbral exacto 50.00 entre CONSERVATIVE y MODERATE)
    engine = ScoringEngine(
        conservative_threshold=Decimal("50.00"),
        moderate_threshold=Decimal("80.00"),
    )

    # Act
    category = engine.determine_category(Decimal("50.00"))

    # Assert
    assert category == FinancialCategory.CONSERVATIVE


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
