from fastapi import Depends
from sqlalchemy.orm import Session

from src.categorization.engine import ScoringEngine
from src.categorization.repository import (
    ProfileRepository,
    SqlAlchemyProfileRepository,
)
from src.categorization.service import CategorizationService
from src.core.database import get_db
from src.survey.repository import SqlAlchemySurveyRepository, SurveyRepository
from src.survey.service import SurveyManager


def get_survey_repository(
    db: Session = Depends(get_db),  # noqa: B008
) -> SurveyRepository:
    """Provee la implementación del repositorio de encuestas para la sesión actual."""
    return SqlAlchemySurveyRepository(db)


def get_profile_repository(
    db: Session = Depends(get_db),  # noqa: B008
) -> ProfileRepository:
    """Provee la implementación del repositorio de perfiles para la sesión actual."""
    return SqlAlchemyProfileRepository(db)


def get_scoring_engine() -> ScoringEngine:
    """Provee la instancia del motor matemático de categorización (BR-05)."""
    return ScoringEngine()


def get_categorization_service(
    scoring_engine: ScoringEngine = Depends(get_scoring_engine),  # noqa: B008
    profile_repo: ProfileRepository = Depends(get_profile_repository),  # noqa: B008
) -> CategorizationService:
    """Ensambla CategorizationService inyectando ScoringEngine y ProfileRepository."""
    return CategorizationService(scoring_engine, profile_repo)


def get_survey_manager(
    survey_repo: SurveyRepository = Depends(get_survey_repository),  # noqa: B008
    categorization_service: CategorizationService = Depends(  # noqa: B008
        get_categorization_service
    ),
) -> SurveyManager:
    """Ensambla SurveyManager desacoplando a SurveyRouter de los repositorios."""
    return SurveyManager(survey_repo, categorization_service)
