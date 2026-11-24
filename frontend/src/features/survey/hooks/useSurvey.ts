import { useCallback, useMemo } from "react";
import { SurveyApiPort, surveyApi } from "../api/surveyApi";
import { EvaluationResultResponse, QuestionDto, SurveyDraftResponse } from "../types";
import { useAnswerSaver } from "./useAnswerSaver";
import { useSurveyFeedback } from "./useSurveyFeedback";
import { useSurveyLoader } from "./useSurveyLoader";
import { useSurveyNavigation } from "./useSurveyNavigation";
import { useSurveySubmission } from "./useSurveySubmission";

export interface UseSurveyState {
  draft: SurveyDraftResponse | null;
  sortedQuestions: QuestionDto[];
  currentIndex: number;
  currentQuestion: QuestionDto | null;
  selectedOptionByQuestion: Readonly<Record<number, number>>;
  isLoading: boolean;
  isSavingAnswer: boolean;
  isSubmitting: boolean;
  saveFeedback: string | null;
  errorMessage: string | null;
  result: EvaluationResultResponse | null;
  allRequiredAnswered: boolean;
  selectOption: (questionId: number, selectedOption: number) => Promise<void>;
  goToPreviousQuestion: () => void;
  goToNextQuestion: () => void;
  submitSurvey: () => Promise<void>;
  restartSurvey: () => Promise<void>;
}

function areAllRequiredAnswered(
  questions: QuestionDto[],
  answers: Readonly<Record<number, number>>,
): boolean {
  if (questions.length === 0) {
    return false;
  }
  return questions.every((q) => !q.isRequired || answers[q.questionId] !== undefined);
}

/** Custom hook que orquesta el ciclo de vida de la encuesta (CT-01, CT-06 y CT-09). */
export function useSurvey(api: SurveyApiPort = surveyApi): UseSurveyState {
  const feedback = useSurveyFeedback();
  const loader = useSurveyLoader(api, feedback);
  const saver = useAnswerSaver(api, loader, feedback);
  const navigation = useSurveyNavigation(loader, feedback);
  const submission = useSurveySubmission(api, loader.view.draft, feedback);
  const { sortedQuestions, currentIndex, selectedOptionByQuestion } = loader.view;
  const { loadSurvey } = loader;
  const { resetResult } = submission;

  const allRequiredAnswered = useMemo(
    () => areAllRequiredAnswered(sortedQuestions, selectedOptionByQuestion),
    [sortedQuestions, selectedOptionByQuestion],
  );

  const restartSurvey = useCallback(async () => {
    resetResult();
    await loadSurvey();
  }, [loadSurvey, resetResult]);

  return {
    ...loader.view,
    ...saver,
    ...navigation,
    currentQuestion: sortedQuestions[currentIndex] ?? null,
    errorMessage: feedback.errorMessage,
    saveFeedback: feedback.saveFeedback,
    isSubmitting: submission.isSubmitting,
    result: submission.result,
    submitSurvey: submission.submitSurvey,
    allRequiredAnswered,
    restartSurvey,
  };
}
