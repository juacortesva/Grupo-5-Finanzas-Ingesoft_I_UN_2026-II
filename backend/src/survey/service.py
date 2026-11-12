from uuid import UUID

from src.survey.enums import SurveyStatus
from src.survey.models import SurveyModel
from src.survey.repository import ISurveyRepository
from src.survey.schemas import QuestionDTO, SurveyStartResponse


class SurveyManager:
    """Orquesta el ciclo de vida de la encuesta de onboarding (REQ-01)."""

    def __init__(self, survey_repo: ISurveyRepository) -> None:
        self._survey_repo = survey_repo

    def start_survey(self, user_id: UUID) -> SurveyStartResponse:
        """Inicia una encuesta en DRAFT o devuelve el borrador activo existente."""
        draft = self._survey_repo.find_draft_by_user_id(user_id)
        if draft is None:
            new_survey = SurveyModel(client_id=user_id, status=SurveyStatus.DRAFT.value)
            draft = self._survey_repo.save(new_survey)

        questions = self._survey_repo.get_active_questions()
        return SurveyStartResponse(
            survey_id=draft.survey_id,
            client_id=draft.client_id,
            status=SurveyStatus(draft.status),
            started_at=draft.started_at,
            questions=[QuestionDTO.model_validate(q) for q in questions],
        )
