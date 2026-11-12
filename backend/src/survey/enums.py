from enum import StrEnum


class SurveyStatus(StrEnum):
    """Estados válidos del ciclo de vida de una encuesta."""

    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
