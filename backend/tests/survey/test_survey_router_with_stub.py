"""Uso de `StubSurveyManager` para probar `SurveyRouter` sin base de datos.

Sirve de ejemplo para quien implemente la capa API (CT-01, CT-09): se reemplaza
`get_survey_manager` y `get_current_user` con `app.dependency_overrides`.
"""

from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.core.auth_deps import get_current_user
from src.core.exceptions import NotFoundError
from src.main import app
from src.survey.service import get_survey_manager
from tests.doubles.survey_doubles import StubSurveyManager

USER_ID = uuid4()


@pytest.fixture()
def stub_manager() -> StubSurveyManager:
    return StubSurveyManager()


@pytest.fixture()
def api(stub_manager: StubSurveyManager) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_survey_manager] = lambda: stub_manager
    app.dependency_overrides[get_current_user] = lambda: USER_ID
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_start_survey_when_stubbed_then_returns_draft_without_weights(
    api: TestClient, stub_manager: StubSurveyManager
) -> None:
    # Act
    response = api.post("/api/surveys")

    # Assert (CT-01 oculta weight y value de las opciones)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DRAFT"
    assert "weight" not in body["questions"][0]
    assert body["questions"][0]["options"][0] == {
        "selectedOption": 1,
        "label": "Opción 1",
    }
    assert stub_manager.calls == ["start_survey"]


def test_complete_survey_when_stubbed_then_returns_score_as_string(
    api: TestClient,
) -> None:
    # Act
    response = api.post(f"/api/surveys/{uuid4()}/complete")

    # Assert (CT-09: totalScore viaja como string para conservar el Decimal)
    assert response.status_code == 200
    assert response.json()["assignedCategory"] == "MODERATE"
    assert response.json()["totalScore"] == "65.00"


def test_complete_survey_when_manager_raises_not_found_then_returns_404(
    api: TestClient, stub_manager: StubSurveyManager
) -> None:
    # Arrange
    stub_manager.error = NotFoundError("Encuesta no encontrada")

    # Act
    response = api.post(f"/api/surveys/{uuid4()}/complete")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Encuesta no encontrada"}
