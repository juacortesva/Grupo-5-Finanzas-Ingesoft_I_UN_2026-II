from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.survey.enums import SurveyStatus
from src.survey.repository import ISurveyRepository, get_survey_repository
from src.survey.schemas import QuestionDTO, SurveyStartResponse


class SurveyManager:
    """Orquesta el ciclo de vida de la encuesta de onboarding (REQ-01).

    Colabora solo con la interfaz `ISurveyRepository`; no conoce SQLAlchemy
    ni objetos HTTP (`01_Architectural_and_Detailed_Design.md` §3).
    """

    def __init__(self, survey_repo: ISurveyRepository) -> None:
        self._survey_repo = survey_repo

    def start_survey(self, user_id: UUID) -> SurveyStartResponse:
        """Inicia una encuesta en `DRAFT` o devuelve el borrador activo existente.

        Contrato `startSurvey(userId)` (diseño 02 §3): idempotente, a lo sumo
        un `DRAFT` por cliente (REQ-01 Escenario 2).

        Args:
            user_id: Identificador del cliente autenticado.

        Returns:
            La encuesta en `DRAFT` con el catálogo activo de preguntas (BR-02).
        """
        draft = self._survey_repo.find_draft_by_user_id(user_id)
        if draft is None:
            draft = self._survey_repo.create_draft(user_id)

        questions = self._survey_repo.get_active_questions()
        return SurveyStartResponse(
            survey_id=draft.survey_id,
            client_id=draft.client_id,
            status=SurveyStatus(draft.status),
            started_at=draft.started_at,
            questions=[QuestionDTO.model_validate(q) for q in questions],
        )


def get_survey_manager(
    survey_repo: Annotated[ISurveyRepository, Depends(get_survey_repository)],
) -> SurveyManager:
    """Construye `SurveyManager` con su repositorio (inyección de dependencias)."""
    return SurveyManager(survey_repo)
