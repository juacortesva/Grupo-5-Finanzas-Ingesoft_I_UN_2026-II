import { beforeEach, describe, expect, it } from "vitest";
import { EvaluationStatus, FinancialCategory, SurveyStatus } from "../types";
import { mockSurveyApi, resetMockSurveyState } from "./mockSurveyApi";

describe("mockSurveyApi", () => {
  beforeEach(() => {
    resetMockSurveyState();
  });

  it("test_start_survey_when_called_twice_then_returns_same_draft_idempotently", async () => {
    // Arrange
    const firstDraft = await mockSurveyApi.startSurvey();

    // Act
    const secondDraft = await mockSurveyApi.startSurvey();

    // Assert
    expect(firstDraft.status).toBe(SurveyStatus.DRAFT);
    expect(secondDraft.surveyId).toBe(firstDraft.surveyId);
    expect(firstDraft.questions.length).toBeLessThanOrEqual(10);
  });

  it("test_save_answer_when_survey_completed_then_rejects_with_409", async () => {
    // Arrange
    const draft = await mockSurveyApi.startSurvey();
    resetMockSurveyState({ status: SurveyStatus.COMPLETED });

    // Act & Assert
    await expect(
      mockSurveyApi.saveAnswer(draft.surveyId, { questionId: 1, selectedOption: 2 }),
    ).rejects.toMatchObject({ status: 409 });
  });

  it("test_complete_survey_when_eval_fails_then_returns_under_evaluation", async () => {
    // Arrange
    resetMockSurveyState({ simulateEvaluationError: true });
    const draft = await mockSurveyApi.startSurvey();
    for (const question of draft.questions) {
      await mockSurveyApi.saveAnswer(draft.surveyId, {
        questionId: question.questionId,
        selectedOption: 2,
      });
    }

    // Act
    const result = await mockSurveyApi.completeSurvey(draft.surveyId);

    // Assert
    expect(result.evaluationStatus).toBe(EvaluationStatus.ERROR);
    expect(result.assignedCategory).toBe(FinancialCategory.UNDER_EVALUATION);
    expect(result.totalScore).toBeNull();
  });
});
