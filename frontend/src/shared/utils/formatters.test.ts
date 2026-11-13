import { describe, expect, it } from "vitest";
import { QuestionDto } from "../../features/survey/types";
import { findNextPendingQuestionIndex, formatDecimalScore } from "./formatters";

describe("formatters", () => {
  it("test_format_decimal_score_when_valid_string_then_preserves_two_decimals", () => {
    // Arrange
    const rawScore = "57.5";

    // Act
    const formatted = formatDecimalScore(rawScore);

    // Assert
    expect(formatted).toBe("57.50");
  });

  it("test_format_decimal_score_when_null_then_returns_unavailable_label", () => {
    // Arrange
    const rawScore = null;

    // Act
    const formatted = formatDecimalScore(rawScore);

    // Assert
    expect(formatted).toBe("No disponible");
  });

  it("test_find_next_pending_when_partial_answers_then_returns_first_unanswered", () => {
    // Arrange
    const questions: QuestionDto[] = [
      {
        questionId: 1,
        text: "Pregunta 1",
        displayOrder: 1,
        isRequired: true,
        options: [{ selectedOption: 1, label: "Opción 1" }],
      },
      {
        questionId: 2,
        text: "Pregunta 2",
        displayOrder: 2,
        isRequired: true,
        options: [{ selectedOption: 1, label: "Opción 1" }],
      },
      {
        questionId: 3,
        text: "Pregunta 3",
        displayOrder: 3,
        isRequired: true,
        options: [{ selectedOption: 1, label: "Opción 1" }],
      },
    ];
    const savedAnswers = [{ questionId: 1, selectedOption: 1 }];

    // Act
    const nextIndex = findNextPendingQuestionIndex(questions, savedAnswers);

    // Assert
    expect(nextIndex).toBe(1);
  });
});
