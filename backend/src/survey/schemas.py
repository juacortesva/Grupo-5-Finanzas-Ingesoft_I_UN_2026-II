from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.core.schemas import CamelCaseSchema
from src.survey.enums import SurveyStatus


class QuestionDTO(CamelCaseSchema):
    """Pregunta parametrizada expuesta al cliente web."""

    question_id: int
    text: str
    weight: Decimal
    display_order: int
    is_required: bool


class SurveyStartResponse(CamelCaseSchema):
    """Respuesta al iniciar o recuperar el borrador de encuesta (REQ-01)."""

    survey_id: UUID
    client_id: UUID
    status: SurveyStatus
    started_at: datetime
    questions: list[QuestionDTO]
