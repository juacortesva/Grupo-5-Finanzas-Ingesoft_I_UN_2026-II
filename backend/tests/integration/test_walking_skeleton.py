from decimal import Decimal

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_start_survey_when_demo_user_then_returns_draft_and_questions() -> None:
    # Arrange & Act
    response = client.post("/api/v1/surveys/start")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert payload["status"] == "DRAFT"
    assert payload["clientId"] == "11111111-1111-1111-1111-111111111111"
    assert len(payload["questions"]) == 3
    assert Decimal(payload["questions"][0]["weight"]) == Decimal("0.4000")
