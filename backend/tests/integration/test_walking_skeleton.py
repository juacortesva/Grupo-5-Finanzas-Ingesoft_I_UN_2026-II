"""Prueba E2E del Walking Skeleton: Router -> Service -> Repository -> PostgreSQL."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.categorization.models import FinancialProfileModel
from src.survey.enums import SurveyStatus
from src.survey.models import QuestionModel, SurveyModel
from src.survey.repository import SqlAlchemySurveyRepository


def test_health_when_database_available_then_returns_ok(
    api_client: TestClient,
) -> None:
    # Arrange: la fixture provee una conexión real a PostgreSQL.

    # Act
    response = api_client.get("/api/v1/health")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.usefixtures("isolated_catalog")
def test_start_survey_when_registered_client_then_returns_draft_and_questions(
    api_client: TestClient, registered_client: UUID
) -> None:
    # Arrange
    headers = {"X-User-Id": str(registered_client)}

    # Act
    response = api_client.post("/api/v1/surveys/start", headers=headers)
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert payload["status"] == "DRAFT"
    assert payload["clientId"] == str(registered_client)
    assert [q["displayOrder"] for q in payload["questions"]] == [1, 2, 3]
    assert payload["questions"][0]["weight"] == "0.4000"
    assert Decimal(payload["questions"][0]["weight"]) == Decimal("0.4000")


@pytest.mark.usefixtures("isolated_catalog")
def test_start_survey_when_draft_exists_then_returns_same_draft(
    api_client: TestClient, registered_client: UUID
) -> None:
    # Arrange
    headers = {"X-User-Id": str(registered_client)}
    first = api_client.post("/api/v1/surveys/start", headers=headers).json()

    # Act
    second = api_client.post("/api/v1/surveys/start", headers=headers).json()

    # Assert
    assert second["surveyId"] == first["surveyId"]


def test_start_survey_when_client_not_registered_then_returns_401(
    api_client: TestClient,
) -> None:
    # Arrange
    headers = {"X-User-Id": str(uuid4())}

    # Act
    response = api_client.post("/api/v1/surveys/start", headers=headers)

    # Assert
    assert response.status_code == 401


def test_start_survey_when_user_id_header_invalid_then_returns_401(
    api_client: TestClient,
) -> None:
    # Arrange
    headers = {"X-User-Id": "no-es-un-uuid"}

    # Act
    response = api_client.post("/api/v1/surveys/start", headers=headers)

    # Assert
    assert response.status_code == 401


@dataclass(frozen=True)
class InvalidProfileCase:
    """Perfil que viola un invariante de `financial_profile` (diseño 02 §2.2)."""

    category: str
    status: str
    score: Decimal | None


INVALID_PROFILES = [
    # REQ-01 Escenario 3: ERROR exige total_score nulo.
    InvalidProfileCase("UNDER_EVALUATION", "ERROR", Decimal("1.0000")),
    # REQ-01 Escenario 3: ERROR exige UNDER_EVALUATION.
    InvalidProfileCase("MODERATE", "ERROR", None),
    # Catálogo cerrado de FinancialCategory.
    InvalidProfileCase("RISKY", "COMPLETED", Decimal("1.0000")),
]


@pytest.mark.parametrize("case", INVALID_PROFILES)
def test_save_profile_when_violates_design_invariant_then_database_rejects(
    db_session: Session, registered_client: UUID, case: InvalidProfileCase
) -> None:
    # Arrange
    survey = SurveyModel(client_id=registered_client)
    db_session.add(survey)
    db_session.flush()
    profile = FinancialProfileModel(
        client_id=registered_client,
        survey_id=survey.survey_id,
        assigned_category=case.category,
        evaluation_status=case.status,
        total_score=case.score,
    )
    db_session.add(profile)

    # Act & Assert
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_save_question_when_negative_weight_then_database_rejects(
    db_session: Session,
) -> None:
    # Arrange
    question = QuestionModel(text="x", weight=Decimal("-0.1000"), display_order=99)
    db_session.add(question)

    # Act & Assert
    with pytest.raises(IntegrityError):
        db_session.flush()


@pytest.mark.usefixtures("isolated_catalog")
def test_save_question_when_exceeds_ten_active_then_database_rejects(
    db_session: Session,
) -> None:
    # Arrange (BR-02: el catálogo aislado ya tiene 3 preguntas activas)
    extra = [
        QuestionModel(text=f"Extra {n}", weight=Decimal("0.0000"), display_order=n)
        for n in range(4, 12)
    ]
    db_session.add_all(extra)

    # Act & Assert
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_update_survey_when_completed_at_changes_then_database_rejects(
    db_session: Session, registered_client: UUID
) -> None:
    # Arrange
    completed_at = datetime(2026, 11, 12, tzinfo=UTC)
    survey = SurveyModel(
        client_id=registered_client,
        status=SurveyStatus.COMPLETED.value,
        completed_at=completed_at,
    )
    db_session.add(survey)
    db_session.flush()
    survey.status = SurveyStatus.DRAFT.value
    survey.completed_at = None

    # Act & Assert
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_create_draft_when_draft_already_exists_then_returns_existing(
    db_session: Session, registered_client: UUID
) -> None:
    # Arrange (simula la carrera de diseño 02 §2.4: otra petición creó el DRAFT)
    repository = SqlAlchemySurveyRepository(db_session)
    winner = repository.create_draft(registered_client)

    # Act
    loser = repository.create_draft(registered_client)

    # Assert
    assert loser.survey_id == winner.survey_id
