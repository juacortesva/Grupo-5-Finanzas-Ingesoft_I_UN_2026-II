import { useCallback } from "react";
import { SurveyFeedback } from "./useSurveyFeedback";
import { SurveyLoader } from "./useSurveyLoader";

export interface SurveyNavigationActions {
  goToPreviousQuestion: () => void;
  goToNextQuestion: () => void;
}

/** Avanza o retrocede entre las preguntas del borrador. */
export function useSurveyNavigation(
  loader: SurveyLoader,
  feedback: SurveyFeedback,
): SurveyNavigationActions {
  const { setCurrentIndex } = loader;
  const questionCount = loader.view.sortedQuestions.length;
  const { setSaveFeedback } = feedback;

  const goToPreviousQuestion = useCallback(() => {
    setCurrentIndex((prev) => Math.max(0, prev - 1));
    setSaveFeedback(null);
  }, [setCurrentIndex, setSaveFeedback]);

  const goToNextQuestion = useCallback(() => {
    setCurrentIndex((prev) => Math.min(questionCount - 1, prev + 1));
    setSaveFeedback(null);
  }, [questionCount, setCurrentIndex, setSaveFeedback]);

  return { goToPreviousQuestion, goToNextQuestion };
}
