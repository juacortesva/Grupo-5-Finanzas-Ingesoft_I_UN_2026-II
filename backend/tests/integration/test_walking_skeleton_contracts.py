from uuid import uuid4

from fastapi.testclient import TestClient

AUTH_USER_1 = {"Authorization": "Bearer dev-user-1"}
AUTH_USER_2 = {"Authorization": "Bearer dev-user-2"}


def test_start_survey_when_unauthenticated_then_returns_401(
    client: TestClient,
) -> None:
    # Act
    response = client.post("/api/surveys")

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail": "No autenticado"}


def test_start_survey_when_authenticated_then_returns_draft_with_question_options(
    client: TestClient,
) -> None:
    # Act
    response = client.post("/api/surveys", headers=AUTH_USER_1)

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DRAFT"
    assert len(body["questions"]) == 2
    first_option = body["questions"][0]["options"][0]
    assert set(first_option.keys()) == {"id", "optionNumber", "text"}
    assert "weight" not in body["questions"][0]


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
    response = client.post(
        f"/api/surveys/{survey_id}/complete", headers=AUTH_USER_1
    )

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
    completed = client.post(
        f"/api/surveys/{survey_id}/complete", headers=AUTH_USER_1
    )
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
    assert isinstance(result["totalScore"], str)
    assert mutate_after.status_code == 409
    assert complete_twice.status_code == 409
    assert "detail" in mutate_after.json()
