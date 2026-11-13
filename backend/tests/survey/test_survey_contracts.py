from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.categorization.models import FinancialProfileModel
from src.core.config import Settings, settings
from src.survey.enums import SurveyStatus
from src.survey.models import AnswerModel, QuestionModel, SurveyModel
from src.survey.repository import SqlAlchemySurveyRepository
from src.survey.schemas import Answer

AUTH_USER_1 = {"Authorization": "Bearer dev-user-1"}
AUTH_USER_2 = {"Authorization": "Bearer dev-user-2"}


def test_settings_when_database_url_missing_then_raises_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # Act & Assert
    with pytest.raises(PydanticValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_start_survey_when_unauthenticated_then_returns_401(
    client: TestClient,
) -> None:
    # Arrange & Act
    response = client.post("/api/surveys")

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "No autenticado"}


def test_start_survey_when_authenticated_then_returns_draft_with_question_options(
    client: TestClient,
) -> None:
    # Arrange & Act
    response = client.post("/api/surveys", headers=AUTH_USER_1)

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DRAFT"
    assert len(body["questions"]) == 2
    first_option = body["questions"][0]["options"][0]
    assert set(first_option.keys()) == {"selectedOption", "label"}
    assert "weight" not in body["questions"][0]


def test_start_survey_when_draft_already_exists_then_returns_same_survey_id(
    client: TestClient,
) -> None:
    # Arrange
    first = client.post("/api/surveys", headers=AUTH_USER_1).json()

    # Act
    second = client.post("/api/surveys", headers=AUTH_USER_1).json()

    # Assert (BR-02: idempotencia sobre el único DRAFT activo del cliente)
    assert second["surveyId"] == first["surveyId"]


def test_save_answer_when_other_user_or_nonexistent_then_returns_404(
    client: TestClient,
) -> None:
    # Arrange
    draft = client.post("/api/surveys", headers=AUTH_USER_1).json()
    survey_id = draft["surveyId"]

    # Act
    res_other = client.put(
        f"/api/surveys/{survey_id}/answers",
        headers=AUTH_USER_2,
        json={"questionId": 1, "selectedOption": 1},
    )
    res_missing = client.put(
        f"/api/surveys/{uuid4()}/answers",
        headers=AUTH_USER_1,
        json={"questionId": 1, "selectedOption": 1},
    )

    # Assert
    assert res_other.status_code == 404
    assert res_missing.status_code == 404
    assert "detail" in res_other.json()


def test_save_answer_when_invalid_option_then_returns_422(
    client: TestClient,
) -> None:
    # Arrange
    draft = client.post("/api/surveys", headers=AUTH_USER_1).json()
    survey_id = draft["surveyId"]

    # Act
    response = client.put(
        f"/api/surveys/{survey_id}/answers",
        headers=AUTH_USER_1,
        json={"questionId": 1, "selectedOption": 999},
    )

    # Assert
    assert response.status_code == 422
    assert "detail" in response.json()


def test_complete_survey_when_missing_required_answers_then_returns_422(
    client: TestClient,
) -> None:
    # Arrange
    draft = client.post("/api/surveys", headers=AUTH_USER_1).json()
    survey_id = draft["surveyId"]

    # Act
    response = client.post(f"/api/surveys/{survey_id}/complete", headers=AUTH_USER_1)

    # Assert
    assert response.status_code == 422
    assert "detail" in response.json()


def test_complete_survey_when_all_answered_then_returns_200_and_blocks_mutations_409(
    client: TestClient,
) -> None:
    # Arrange
    draft = client.post("/api/surveys", headers=AUTH_USER_1).json()
    survey_id = draft["surveyId"]
    res1 = client.put(
        f"/api/surveys/{survey_id}/answers",
        headers=AUTH_USER_1,
        json={"questionId": 1, "selectedOption": 2},
    )
    res2 = client.put(
        f"/api/surveys/{survey_id}/answers",
        headers=AUTH_USER_1,
        json={"questionId": 2, "selectedOption": 2},
    )
    assert res1.status_code == 204
    assert res2.status_code == 204

    # Act
    completed = client.post(f"/api/surveys/{survey_id}/complete", headers=AUTH_USER_1)
    mutate_after = client.put(
        f"/api/surveys/{survey_id}/answers",
        headers=AUTH_USER_1,
        json={"questionId": 1, "selectedOption": 1},
    )
    complete_twice = client.post(
        f"/api/surveys/{survey_id}/complete", headers=AUTH_USER_1
    )

    # Assert
    assert completed.status_code == 200
    result = completed.json()
    assert result["surveyId"] == survey_id
    assert result["evaluationStatus"] == "COMPLETED"
    assert result["assignedCategory"] == "MODERATE"
    assert result["totalScore"] == "65.00"
    assert mutate_after.status_code == 409
    assert complete_twice.status_code == 409
    assert "detail" in mutate_after.json()


def test_partial_unique_index_when_second_draft_inserted_then_raises_integrity_error(
    db_session: Session,
) -> None:
    # Arrange
    user_id = UUID(settings.dev_user_1_id)
    first_draft = SurveyModel(client_id=user_id, status="DRAFT")
    db_session.add(first_draft)
    db_session.commit()

    # Act & Assert (BR-02 / ADR-0004: índice único parcial sobre status = 'DRAFT')
    second_draft = SurveyModel(client_id=user_id, status="DRAFT")
    db_session.add(second_draft)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Al pasar la primera a COMPLETED, se permite crear un nuevo DRAFT
    first_draft.status = "COMPLETED"
    db_session.commit()
    new_draft = SurveyModel(client_id=user_id, status="DRAFT")
    db_session.add(new_draft)
    db_session.commit()
    assert new_draft.survey_id != first_draft.survey_id


def test_numeric_columns_when_persisted_then_preserve_exact_decimal_type(
    client: TestClient,
    db_session: Session,
) -> None:
    # Arrange
    draft = client.post("/api/surveys", headers=AUTH_USER_1).json()
    survey_id = draft["surveyId"]
    client.put(
        f"/api/surveys/{survey_id}/answers",
        headers=AUTH_USER_1,
        json={"questionId": 1, "selectedOption": 2},
    )
    client.put(
        f"/api/surveys/{survey_id}/answers",
        headers=AUTH_USER_1,
        json={"questionId": 2, "selectedOption": 2},
    )
    client.post(f"/api/surveys/{survey_id}/complete", headers=AUTH_USER_1)

    # Act
    question = db_session.execute(
        select(QuestionModel).where(QuestionModel.question_id == 1)
    ).scalar_one()
    answer = db_session.execute(select(AnswerModel)).scalars().first()
    profile = db_session.execute(select(FinancialProfileModel)).scalar_one()

    # Assert (ADR-0001: cero float, Numeric(10, 2, asdecimal=True))
    assert isinstance(question.weight, Decimal)
    assert isinstance(question.options[0].value, Decimal)
    assert answer is not None
    assert isinstance(answer.option_value, Decimal)
    assert isinstance(profile.total_score, Decimal)
    assert profile.total_score == Decimal("65.00")


def test_repository_for_update_when_survey_completed_then_rejects_mutations(
    client: TestClient,
    db_session: Session,
) -> None:
    # Arrange
    user_id = UUID(settings.dev_user_1_id)
    draft = client.post("/api/surveys", headers=AUTH_USER_1).json()
    survey_id = UUID(draft["surveyId"])
    repo = SqlAlchemySurveyRepository(db_session)

    # Act: cierre mediante update_status (ejecuta SELECT ... FOR UPDATE)
    closed = repo.update_status(survey_id, user_id, SurveyStatus.COMPLETED)
    duplicate_close = repo.update_status(survey_id, user_id, SurveyStatus.COMPLETED)
    late_answer = repo.save_answer(
        survey_id,
        user_id,
        Answer(
            question_id=1,
            selected_option=1,
            option_value=Decimal("15.00"),
        ),
    )

    # Assert (BR-03 / ADR-0004)
    assert closed is not None
    assert closed.status == SurveyStatus.COMPLETED
    assert duplicate_close is None
    assert late_answer is False
