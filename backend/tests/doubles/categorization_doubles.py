"""Dobles del Módulo Categorization.

- `InMemoryProfileRepository` (fake): cumple el `Protocol` `ProfileRepository`
  (CT-12) con upsert por `user_id` en un diccionario (BR-04).
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.categorization.schemas import FinancialProfile, ProfileEvaluation


class InMemoryProfileRepository:
    """Fake de `ProfileRepository`: un perfil vigente por cliente (BR-04)."""

    def __init__(self) -> None:
        self.profiles: dict[UUID, FinancialProfile] = {}
        self.received: list[ProfileEvaluation] = []

    def save_category(
        self, user_id: UUID, evaluation: ProfileEvaluation
    ) -> FinancialProfile:
        self.received.append(evaluation)
        profile = FinancialProfile(
            profile_id=uuid4(),
            user_id=user_id,
            survey_id=evaluation.survey_id,
            assigned_category=evaluation.assigned_category,
            evaluation_status=evaluation.evaluation_status,
            total_score=evaluation.total_score,
            assigned_at=datetime.now(UTC),
        )
        self.profiles[user_id] = profile  # Upsert: un perfil vigente (BR-04).
        return profile

    def find_by_user_id(self, user_id: UUID) -> FinancialProfile | None:
        return self.profiles.get(user_id)
