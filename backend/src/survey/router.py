from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.auth_deps import get_current_user
from src.core.database import get_db
from src.survey.repository import SqlAlchemySurveyRepository
from src.survey.schemas import SurveyStartResponse
from src.survey.service import SurveyManager

router = APIRouter(prefix="/surveys", tags=["Surveys"])


def get_survey_manager(db: Annotated[Session, Depends(get_db)]) -> SurveyManager:
    """Construye la instancia de SurveyManager con su repositorio."""
    return SurveyManager(SqlAlchemySurveyRepository(db))


@router.post(
    "/start",
    response_model=SurveyStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Inicia o recupera el borrador activo de la encuesta financiera",
)
def start_survey(
    user_id: Annotated[UUID, Depends(get_current_user)],
    manager: Annotated[SurveyManager, Depends(get_survey_manager)],
) -> SurveyStartResponse:
    """Endpoint E2E para iniciar onboarding y obtener catálogo de preguntas."""
    return manager.start_survey(user_id)
