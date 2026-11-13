from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from src.categorization.engine import ScoringEngine
from src.categorization.repository import SqlAlchemyProfileRepository
from src.categorization.schemas import EvaluationResult
from src.categorization.service import CategorizationService
from src.core.auth_deps import get_current_user
from src.core.database import get_db
from src.core.schemas import ErrorResponse
from src.survey.repository import SqlAlchemySurveyRepository
from src.survey.schemas import (
    AnswerDTO,
    QuestionDTO,
    QuestionOptionDTO,
    SaveAnswerRequest,
    Survey,
    SurveyDraftResponse,
)
from src.survey.service import SurveyManager

router = APIRouter(prefix="/api/surveys", tags=["Surveys"])


def _build_survey_manager(db: Session = Depends(get_db)) -> SurveyManager:  # noqa: B008
    survey_repo = SqlAlchemySurveyRepository(db)
    profile_repo = SqlAlchemyProfileRepository(db)
    categorization_service = CategorizationService(ScoringEngine(), profile_repo)
    return SurveyManager(survey_repo, categorization_service)


def _to_draft_response(survey: Survey) -> SurveyDraftResponse:
    return SurveyDraftResponse(
        survey_id=survey.survey_id,
        status=survey.status,
        started_at=survey.started_at,
        questions=[
            QuestionDTO(
                question_id=q.question_id,
                text=q.text,
                display_order=q.display_order,
                is_required=q.is_required,
                options=[
                    QuestionOptionDTO(
                        id=opt.id,
                        option_number=opt.option_number,
                        text=opt.text,
                    )
                    for opt in q.options
                ],
            )
            for q in survey.questions
        ],
        answers=[
            AnswerDTO(
                question_id=ans.question_id,
                selected_option=ans.selected_option,
            )
            for ans in survey.answers
        ],
    )


@router.post(
    "",
    response_model=SurveyDraftResponse,
    status_code=status.HTTP_200_OK,
    responses={401: {"model": ErrorResponse}},
)
def start_survey(
    user_id: UUID = Depends(get_current_user),  # noqa: B008
    manager: SurveyManager = Depends(_build_survey_manager),  # noqa: B008
) -> SurveyDraftResponse:
    """Inicia o recupera el único borrador DRAFT del cliente (CT-01)."""
    survey = manager.start_survey(user_id)
    return _to_draft_response(survey)


@router.put(
    "/{survey_id}/answers",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def save_answer(
    survey_id: UUID,
    payload: SaveAnswerRequest,
    user_id: UUID = Depends(get_current_user),  # noqa: B008
    manager: SurveyManager = Depends(_build_survey_manager),  # noqa: B008
) -> Response:
    """Registra o actualiza una respuesta en el borrador DRAFT (CT-06)."""
    manager.save_answer(survey_id, user_id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{survey_id}/complete",
    response_model=EvaluationResult,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def complete_survey(
    survey_id: UUID,
    user_id: UUID = Depends(get_current_user),  # noqa: B008
    manager: SurveyManager = Depends(_build_survey_manager),  # noqa: B008
) -> EvaluationResult:
    """Cierra la encuesta DRAFT y evalúa el perfil financiero (CT-09)."""
    return manager.complete_survey(survey_id, user_id)
