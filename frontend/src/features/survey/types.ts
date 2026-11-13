/** Tipos de dominio y DTOs del módulo de encuesta alineados con CT-01, CT-06 y CT-09. */

export const SurveyStatus = {
  DRAFT: "DRAFT",
  COMPLETED: "COMPLETED",
} as const;

export type SurveyStatus = (typeof SurveyStatus)[keyof typeof SurveyStatus];

export const FinancialCategory = {
  CONSERVATIVE: "CONSERVATIVE",
  MODERATE: "MODERATE",
  AGGRESSIVE: "AGGRESSIVE",
  UNDER_EVALUATION: "UNDER_EVALUATION",
} as const;

export type FinancialCategory = (typeof FinancialCategory)[keyof typeof FinancialCategory];

export const EvaluationStatus = {
  COMPLETED: "COMPLETED",
  ERROR: "ERROR",
} as const;

export type EvaluationStatus = (typeof EvaluationStatus)[keyof typeof EvaluationStatus];

export interface AnswerOptionDto {
  selectedOption: number;
  label: string;
}

export interface QuestionDto {
  questionId: number;
  text: string;
  displayOrder: number;
  isRequired: boolean;
  options: AnswerOptionDto[];
}

export interface AnswerDto {
  questionId: number;
  selectedOption: number;
}

export interface SurveyDraftResponse {
  surveyId: string;
  status: SurveyStatus;
  startedAt: string;
  questions: QuestionDto[];
  answers: AnswerDto[];
}

export interface SaveAnswerRequest {
  questionId: number;
  selectedOption: number;
}

export interface EvaluationResultResponse {
  surveyId: string;
  assignedCategory: FinancialCategory;
  evaluationStatus: EvaluationStatus;
  /** Puntaje decimal serializado como string desde el backend; null en ERROR (BR-06). */
  totalScore: string | null;
}
