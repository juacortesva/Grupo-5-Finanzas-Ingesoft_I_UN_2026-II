from enum import StrEnum


class FinancialCategory(StrEnum):
    """Categorías financieras iniciales asignadas al cliente (BR-04, BR-06)."""

    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"
    UNDER_EVALUATION = "UNDER_EVALUATION"


class EvaluationStatus(StrEnum):
    """Estados posibles del resultado de evaluación de perfil."""

    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
