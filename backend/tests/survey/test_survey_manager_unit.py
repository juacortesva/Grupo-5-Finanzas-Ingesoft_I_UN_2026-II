"""Pruebas unitarias de `SurveyManager` con dobles en memoria (sin base de datos).

Cada prueba corresponde a una postcondición o a una fila de la tabla de fallos
de CT-03 (start_survey) y CT-09 (complete_survey).
"""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.categorization.enums import EvaluationStatus
from src.core.exceptions import InvalidStateError, NotFoundError, ValidationError
from src.survey.enums import SurveyStatus
from src.survey.schemas import Answer, Survey
from src.survey.service import SurveyManager
from tests.doubles.survey_doubles import (
    InMemorySurveyRepository,
    StubCategorizationService,
    build_catalog,
    build_survey,
)

USER_ID = uuid4()
OTHER_USER_ID = uuid4()


def _make_manager(
    repo: InMemorySurveyRepository | None = None,
    stub: StubCategorizationService | None = None,
) -> tuple[SurveyManager, InMemorySurveyRepository, StubCategorizationService]:
    repo = repo or InMemorySurveyRepository(build_catalog())
    stub = stub or StubCategorizationService()
    return SurveyManager(repo, stub), repo, stub


def _answered_draft(repo: InMemorySurveyRepository, user_id: UUID) -> Survey:
    answers = [
        Answer(question_id=q.question_id, selected_option=1, option_value=Decimal("10"))
        for q in repo.questions
    ]
    return repo.add(build_survey(user_id, repo.questions, answers))


# ---------------------------------------------------------------- CT-03


def test_start_survey_when_no_draft_then_creates_draft_with_catalog() -> None:
    # Arrange
    manager, repo, _ = _make_manager()

    # Act
    survey = manager.start_survey(USER_ID)

    # Assert
    assert survey.status == SurveyStatus.DRAFT
    assert survey.user_id == USER_ID
    assert len(survey.questions) == len(repo.questions)
    assert survey.answers == []
    assert repo.find_draft_by_user_id(USER_ID) == survey


def test_start_survey_when_draft_exists_then_returns_same_draft_br02() -> None:
    # Arrange
    manager, repo, _ = _make_manager()
    existing = repo.add(build_survey(USER_ID, repo.questions))

    # Act
    survey = manager.start_survey(USER_ID)

    # Assert
    assert survey.survey_id == existing.survey_id
    assert repo.save_calls == 0


@pytest.mark.parametrize("catalog_size", [0, 11])
def test_start_survey_when_catalog_out_of_bounds_then_raises_br01(
    catalog_size: int,
) -> None:
    # Arrange
    repo = InMemorySurveyRepository(build_catalog(catalog_size))
    manager, _, _ = _make_manager(repo)

    # Act & Assert
    with pytest.raises(RuntimeError):
        manager.start_survey(USER_ID)
    assert repo.surveys == {}


def test_start_survey_when_persistence_fails_then_propagates_error() -> None:
    # Arrange
    manager, repo, _ = _make_manager()
    repo.fail_on_save = True

    # Act & Assert
    with pytest.raises(RuntimeError):
        manager.start_survey(USER_ID)
    assert repo.surveys == {}


# ---------------------------------------------------------------- CT-09


def test_complete_survey_when_all_answered_then_closes_and_evaluates() -> None:
    # Arrange
    manager, repo, stub = _make_manager()
    draft = _answered_draft(repo, USER_ID)

    # Act
    result = manager.complete_survey(draft.survey_id, USER_ID)

    # Assert
    closed = repo.surveys[draft.survey_id]
    assert closed.status == SurveyStatus.COMPLETED
    assert closed.completed_at is not None
    assert result.evaluation_status == EvaluationStatus.COMPLETED
    assert len(stub.calls) == 1
    user_id, survey_id, scored = stub.calls[0]
    assert (user_id, survey_id) == (USER_ID, draft.survey_id)
    assert [a.weight for a in scored] == [q.weight for q in repo.questions]
    assert all(isinstance(a.option_value, Decimal) for a in scored)


def test_complete_survey_when_required_missing_then_stays_draft_br03() -> None:
    # Arrange
    manager, repo, stub = _make_manager()
    draft = repo.add(build_survey(USER_ID, repo.questions))

    # Act & Assert
    with pytest.raises(ValidationError):
        manager.complete_survey(draft.survey_id, USER_ID)
    assert repo.surveys[draft.survey_id].status == SurveyStatus.DRAFT
    assert stub.calls == []


def test_complete_survey_when_already_completed_then_raises_without_evaluating() -> (
    None
):
    # Arrange
    manager, repo, stub = _make_manager()
    closed = repo.add(
        build_survey(USER_ID, repo.questions, status=SurveyStatus.COMPLETED)
    )

    # Act & Assert
    with pytest.raises(InvalidStateError):
        manager.complete_survey(closed.survey_id, USER_ID)
    assert stub.calls == []


def test_complete_survey_when_closed_concurrently_then_raises_invalid_state() -> None:
    # Arrange
    manager, repo, stub = _make_manager()
    draft = _answered_draft(repo, USER_ID)
    repo.simulate_concurrent_close = True

    # Act & Assert
    with pytest.raises(InvalidStateError):
        manager.complete_survey(draft.survey_id, USER_ID)
    assert stub.calls == []


def test_complete_survey_when_survey_of_other_user_then_raises_not_found() -> None:
    # Arrange
    manager, repo, stub = _make_manager()
    foreign = _answered_draft(repo, OTHER_USER_ID)

    # Act & Assert
    with pytest.raises(NotFoundError):
        manager.complete_survey(foreign.survey_id, USER_ID)
    assert repo.surveys[foreign.survey_id].status == SurveyStatus.DRAFT
    assert stub.calls == []
