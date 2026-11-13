import logging
from datetime import UTC, datetime
from uuid import UUID

from src.categorization.engine import ScoringEngine
from src.categorization.enums import EvaluationStatus, FinancialCategory
from src.categorization.repository import ProfileRepository
from src.categorization.schemas import (
    EvaluationResult,
    ProfileEvaluation,
    ScoredAnswerDTO,
)
from src.core.exceptions import EvaluationPersistenceError, InvalidInputError

logger = logging.getLogger(__name__)


class CategorizationService:
    """Orquesta la evaluación síncrona del perfil y su tolerancia a fallos."""

    def __init__(
        self,
        scoring_engine: ScoringEngine,
        profile_repo: ProfileRepository,
    ) -> None:
        self._scoring_engine = scoring_engine
        self._profile_repo = profile_repo

    def evaluate_profile(
        self,
        user_id: UUID,
        survey_id: UUID,
        answers: list[ScoredAnswerDTO],
    ) -> EvaluationResult:
        """Evalúa respuestas de encuesta cerrada y persiste categoría (CT-10)."""
        if not answers:
            raise InvalidInputError("La encuesta no tiene respuestas")

        try:
            total_score = self._scoring_engine.calculate_score(answers)
            category = self._scoring_engine.determine_category(total_score)
            self._profile_repo.save_category(
                user_id,
                ProfileEvaluation(
                    survey_id=survey_id,
                    assigned_category=category,
                    evaluation_status=EvaluationStatus.COMPLETED,
                    total_score=total_score,
                ),
            )
            return EvaluationResult(
                survey_id=survey_id,
                assigned_category=category,
                evaluation_status=EvaluationStatus.COMPLETED,
                total_score=total_score,
            )
        except Exception as err:
            # REQ-01 / BR-06: Log técnico sin respuestas, puntajes ni PII.
            self.log_error(
                error_type=type(err).__name__,
                operation="evaluate_profile",
                timestamp=datetime.now(UTC),
            )
            return self._save_provisional_profile(user_id, survey_id)

    def log_error(
        self, error_type: str, operation: str, timestamp: datetime
    ) -> None:
        """Registra metadatos técnicos del error sin respuestas, puntajes ni PII."""
        logger.error(
            "Error técnico durante evaluación de perfil financiero",
            extra={
                "error_type": error_type,
                "operation": operation,
                "timestamp": timestamp.isoformat(),
            },
        )

    def _save_provisional_profile(
        self, user_id: UUID, survey_id: UUID
    ) -> EvaluationResult:
        """Persiste perfil provisional UNDER_EVALUATION ante fallo (BR-06)."""
        try:
            self._profile_repo.save_category(
                user_id,
                ProfileEvaluation(
                    survey_id=survey_id,
                    assigned_category=FinancialCategory.UNDER_EVALUATION,
                    evaluation_status=EvaluationStatus.ERROR,
                    total_score=None,
                ),
            )
        except Exception as err:
            raise EvaluationPersistenceError(
                "No fue posible registrar el perfil provisional"
            ) from err

        return EvaluationResult(
            survey_id=survey_id,
            assigned_category=FinancialCategory.UNDER_EVALUATION,
            evaluation_status=EvaluationStatus.ERROR,
            total_score=None,
        )
