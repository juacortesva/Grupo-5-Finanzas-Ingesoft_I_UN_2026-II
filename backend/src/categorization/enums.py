from enum import StrEnum


class FinancialCategory(StrEnum):
    """Catálogo cerrado de categorías financieras iniciales (REQ-01)."""

    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"
    UNDER_EVALUATION = "UNDER_EVALUATION"


class EvaluationStatus(StrEnum):
    """Estados posibles del resultado de evaluación del perfil."""

    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
