import { AnswerDto, QuestionDto } from "../../features/survey/types";

/** Formatea un decimal serializado como string sin convertirlo a aritmética flotante. */
export function formatDecimalScore(score: string | null): string {
  if (score === null || score.trim().length === 0) {
    return "No disponible";
  }
  const normalized = score.trim();
  const [integerPart, decimalPart = ""] = normalized.split(".");
  if (!integerPart) {
    return normalized;
  }
  const paddedDecimal = decimalPart.padEnd(2, "0").slice(0, 2);
  return `${integerPart}.${paddedDecimal}`;
}

/**
 * Calcula el índice de la primera pregunta obligatoria sin respuesta (AC-01.2).
 * Si todas las obligatorias están respondidas, retorna el índice de la última pregunta.
 */
export function findNextPendingQuestionIndex(
  questions: QuestionDto[],
  answers: AnswerDto[],
): number {
  if (questions.length === 0) {
    return 0;
  }

  const answeredIds = new Set(answers.map((answer) => answer.questionId));
  const pendingIndex = questions.findIndex(
    (question) => question.isRequired && !answeredIds.has(question.questionId),
  );

  if (pendingIndex >= 0) {
    return pendingIndex;
  }

  return questions.length - 1;
}
