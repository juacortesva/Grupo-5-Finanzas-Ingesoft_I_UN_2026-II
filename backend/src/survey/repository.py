from abc import ABC, abstractmethod
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.survey.enums import SurveyStatus
from src.survey.models import QuestionModel, SurveyModel

MAX_ACTIVE_QUESTIONS = 10


class ISurveyRepository(ABC):
    """Contrato abstracto de acceso a datos del módulo Survey.

    Toda operación sobre `survey` filtra por el `user_id` autenticado
    (Data Ownership, REQ-01 mitigación de riesgo).
    """

    @abstractmethod
    def find_draft_by_user_id(self, user_id: UUID) -> SurveyModel | None:
        """Busca el único borrador activo del cliente autenticado.

        Args:
            user_id: Identificador del cliente autenticado (`client_id`).

        Returns:
            La encuesta en `DRAFT` del cliente, o `None` si no tiene borrador.
        """

    @abstractmethod
    def create_draft(self, user_id: UUID) -> SurveyModel:
        """Crea el borrador del cliente o retorna el que ganó una carrera.

        Args:
            user_id: Identificador del cliente autenticado (`client_id`).

        Returns:
            La única encuesta en `DRAFT` del cliente.
        """

    @abstractmethod
    def get_active_questions(self) -> list[QuestionModel]:
        """Retorna el catálogo activo de preguntas ordenado por `display_order`.

        Returns:
            Hasta `MAX_ACTIVE_QUESTIONS` preguntas activas (BR-02).
        """


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

    def create_draft(self, user_id: UUID) -> SurveyModel:
        survey = SurveyModel(client_id=user_id, status=SurveyStatus.DRAFT.value)
        self._db.add(survey)
        try:
            self._db.commit()
        except IntegrityError:
            # Diseño 02 §2.4: ante conflicto del índice único parcial
            # (client_id) WHERE status = 'DRAFT', se devuelve el borrador
            # que ganó la carrera en lugar de fallar.
            self._db.rollback()
            existing = self.find_draft_by_user_id(user_id)
            if existing is None:
                raise
            return existing
        self._db.refresh(survey)
        return survey

    def get_active_questions(self) -> list[QuestionModel]:
        # BR-02 (REQ-01): encuesta acotada a un máximo de 10 preguntas activas.
        stmt = (
            select(QuestionModel)
            .where(QuestionModel.is_active.is_(True))
            .order_by(QuestionModel.display_order.asc())
            .limit(MAX_ACTIVE_QUESTIONS)
        )
        return list(self._db.scalars(stmt).all())


def get_survey_repository(
    db: Annotated[Session, Depends(get_db)],
) -> ISurveyRepository:
    """Provee la implementación SQLAlchemy del repositorio por petición."""
    return SqlAlchemySurveyRepository(db)
