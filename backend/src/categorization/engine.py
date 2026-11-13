from decimal import ROUND_HALF_UP, Decimal

from src.categorization.enums import FinancialCategory
from src.categorization.schemas import ScoredAnswerDTO
from src.core.exceptions import InvalidInputError


class ScoringEngine:
    """Motor matemático puro en memoria usando aritmética Decimal (CT-11).

    Nota de Fase 0: Los umbrales por defecto (50.00 y 80.00) son valores
    ficticios/provisionales de calibración para el Walking Skeleton, pendientes
    de validación definitiva por parte de producto/finanzas.
    """

    def __init__(
        self,
        # Umbrales provisionales de Fase 0 (pendientes de definición financiera)
        conservative_threshold: Decimal = Decimal("50.00"),
        moderate_threshold: Decimal = Decimal("80.00"),
    ) -> None:
        if conservative_threshold >= moderate_threshold:
            raise ValueError(
                "conservative_threshold debe ser menor que moderate_threshold"
            )
        self._conservative_threshold = conservative_threshold
        self._moderate_threshold = moderate_threshold

    def calculate_score(self, answers: list[ScoredAnswerDTO]) -> Decimal:
        """Calcula el puntaje ponderado total con precisión Decimal (ADR-0001)."""
        if not answers:
            raise InvalidInputError("La encuesta no tiene respuestas")

        total = Decimal("0.00")
        for item in answers:
            if not isinstance(item.option_value, Decimal) or not isinstance(
                item.weight, Decimal
            ):
                raise InvalidInputError("Los valores deben ser Decimal")
            total += item.option_value * item.weight

        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def determine_category(self, score: Decimal) -> FinancialCategory:
        """Asigna la categoría aplicando desempate conservador BR-05."""
        if not isinstance(score, Decimal) or score < Decimal("0"):
            raise InvalidInputError("El puntaje debe ser un Decimal no negativo")

        # BR-05 (REQ-01): En el límite exacto (<=) se asigna la categoría
        # de menor riesgo.
        if score <= self._conservative_threshold:
            return FinancialCategory.CONSERVATIVE
        if score <= self._moderate_threshold:
            return FinancialCategory.MODERATE
        return FinancialCategory.AGGRESSIVE
