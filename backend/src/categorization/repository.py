from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.categorization.enums import EvaluationStatus, FinancialCategory
from src.categorization.models import FinancialProfileModel
from src.categorization.schemas import FinancialProfile, ProfileEvaluation


class ProfileRepository(Protocol):
    """Contrato de persistencia para el perfil financiero vigente (CT-12)."""

    def save_category(
        self, user_id: UUID, evaluation: ProfileEvaluation
    ) -> FinancialProfile:
        """Inserta o actualiza el perfil único vigente del cliente."""

    def find_by_user_id(self, user_id: UUID) -> FinancialProfile | None:
        """Recupera el perfil financiero vigente del cliente autenticado."""


class SqlAlchemyProfileRepository:
    """Implementación SQLAlchemy del repositorio de perfiles financieros."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def save_category(
        self, user_id: UUID, evaluation: ProfileEvaluation
    ) -> FinancialProfile:
        """Ejecuta upsert por client_id sobre financial_profile (BR-04, BR-06)."""
        existing = self._db.execute(
            select(FinancialProfileModel).where(
                FinancialProfileModel.client_id == user_id
            )
        ).scalar_one_or_none()

        now = datetime.now(UTC)
        if existing is None:
            record = FinancialProfileModel(
                client_id=user_id,
                survey_id=evaluation.survey_id,
                assigned_category=evaluation.assigned_category.value,
                evaluation_status=evaluation.evaluation_status.value,
                total_score=evaluation.total_score,
                assigned_at=now,
            )
            self._db.add(record)
        else:
            existing.survey_id = evaluation.survey_id
            existing.assigned_category = evaluation.assigned_category.value
            existing.evaluation_status = evaluation.evaluation_status.value
            existing.total_score = evaluation.total_score
            existing.assigned_at = now
            record = existing

        self._db.commit()
        self._db.refresh(record)
        return self._to_domain(record)

    def find_by_user_id(self, user_id: UUID) -> FinancialProfile | None:
        """Recupera el perfil vigente filtrando por client_id == user_id."""
        record = self._db.execute(
            select(FinancialProfileModel).where(
                FinancialProfileModel.client_id == user_id
            )
        ).scalar_one_or_none()
        if record is None:
            return None
        return self._to_domain(record)

    def _to_domain(self, record: FinancialProfileModel) -> FinancialProfile:
        return FinancialProfile(
            profile_id=record.profile_id,
            user_id=record.client_id,
            survey_id=record.survey_id,
            assigned_category=FinancialCategory(record.assigned_category),
            evaluation_status=EvaluationStatus(record.evaluation_status),
            total_score=record.total_score,
            assigned_at=record.assigned_at,
        )
