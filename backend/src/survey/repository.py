from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.survey.enums import SurveyStatus
from src.survey.models import QuestionModel, SurveyModel


class ISurveyRepository(ABC):
    """Contrato abstracto de acceso a datos del módulo Survey."""

    @abstractmethod
    def find_draft_by_user_id(self, user_id: UUID) -> SurveyModel | None:
        """Busca el único borrador activo del cliente autenticado."""

    @abstractmethod
    def save(self, survey: SurveyModel) -> SurveyModel:
        """Persiste una encuesta en PostgreSQL."""

    @abstractmethod
    def get_active_questions(self) -> list[QuestionModel]:
        """Retorna el catálogo activo de preguntas (BR-02: máx. 10)."""


class SqlAlchemySurveyRepository(ISurveyRepository):
    """Implementación SQLAlchemy del repositorio de encuestas."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def find_draft_by_user_id(self, user_id: UUID) -> SurveyModel | None:
        stmt = select(SurveyModel).where(
            SurveyModel.client_id == user_id,
            SurveyModel.status == SurveyStatus.DRAFT.value,
        )
        return self._db.scalar(stmt)

    def save(self, survey: SurveyModel) -> SurveyModel:
        self._db.add(survey)
        self._db.commit()
        self._db.refresh(survey)
        return survey

    def get_active_questions(self) -> list[QuestionModel]:
        # BR-02 (REQ-01): Encuesta acotada a un máximo de 10 preguntas activas.
        stmt = (
            select(QuestionModel)
            .where(QuestionModel.is_active.is_(True))
            .order_by(QuestionModel.display_order.asc())
            .limit(10)
        )
        return list(self._db.scalars(stmt).all())
