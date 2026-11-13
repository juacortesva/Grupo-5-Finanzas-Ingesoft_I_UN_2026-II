from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.core.schemas import CamelCaseSchema
from src.survey.enums import SurveyStatus


class AnswerOption(BaseModel):
    """Opción de respuesta en dominio (incluye value para uso interno)."""

    id: int
    question_id: int
    option_number: int
    text: str
    value: Decimal


class Question(BaseModel):
    """Pregunta del cuestionario en dominio (incluye weight para evaluación)."""

    question_id: int
    text: str
    weight: Decimal
    display_order: int
    is_required: bool
    options: list[AnswerOption]


class Answer(BaseModel):
    """Respuesta registrada en dominio."""

    question_id: int
    selected_option: int
    option_value: Decimal


class Survey(BaseModel):
    """Entidad de dominio Survey."""

    survey_id: UUID
    user_id: UUID
    status: SurveyStatus
    started_at: datetime
    completed_at: datetime | None
    questions: list[Question]
    answers: list[Answer]


class QuestionOptionDTO(CamelCaseSchema):
    """DTO HTTP de opción de respuesta (oculta value, CT-01)."""

    id: int
    option_number: int
    text: str


class QuestionDTO(CamelCaseSchema):
    """DTO HTTP de pregunta (oculta weight, CT-01)."""

    question_id: int
    text: str
    display_order: int
    is_required: bool
    options: list[QuestionOptionDTO]


class AnswerDTO(CamelCaseSchema):
    """DTO HTTP de respuesta registrada (oculta option_value, CT-01)."""

    question_id: int
    selected_option: int


class SurveyDraftResponse(CamelCaseSchema):
    """Respuesta HTTP de startSurvey (CT-01)."""

    survey_id: UUID
    status: SurveyStatus
    started_at: datetime
    questions: list[QuestionDTO]
    answers: list[AnswerDTO]


class SaveAnswerRequest(BaseModel):
    """Cuerpo HTTP de PUT /api/surveys/{surveyId}/answers (CT-06)."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    question_id: int = Field(ge=1)
    selected_option: int = Field(ge=1)
