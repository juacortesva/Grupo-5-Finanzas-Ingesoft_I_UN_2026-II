from enum import StrEnum


class SurveyStatus(StrEnum):
    """Estados del ciclo de vida de la encuesta (BR-02, BR-03)."""

    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
