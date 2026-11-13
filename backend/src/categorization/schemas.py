from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from src.categorization.enums import EvaluationStatus, FinancialCategory
from src.core.schemas import CamelCaseSchema


class ScoredAnswerDTO(BaseModel):
    """DTO de frontera entre módulos con valores resueltos en Decimal (CT-10)."""

    question_id: int
    option_value: Decimal
    weight: Decimal = Field(ge=Decimal("0"))


class ProfileEvaluation(BaseModel):
    """DTO de entrada para persistir el perfil vigente (CT-12)."""

    survey_id: UUID
    assigned_category: FinancialCategory
    evaluation_status: EvaluationStatus
    total_score: Decimal | None


class FinancialProfile(BaseModel):
    """Entidad de dominio del perfil financiero persistido."""

    profile_id: UUID
    user_id: UUID
    survey_id: UUID
    assigned_category: FinancialCategory
    evaluation_status: EvaluationStatus
    total_score: Decimal | None
    assigned_at: datetime


class EvaluationResult(CamelCaseSchema):
    """Resultado devuelto por evaluate_profile (CT-10) y expuesto en CT-09."""

    survey_id: UUID
    assigned_category: FinancialCategory
    evaluation_status: EvaluationStatus
    total_score: Decimal | None

    @field_serializer("total_score")
    def serialize_total_score(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para preservar precisión en JSON."""
        if value is None:
            return None
        return str(value)
