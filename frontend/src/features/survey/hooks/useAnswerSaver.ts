import { useCallback, useState } from "react";
import { SurveyApiPort } from "../api/surveyApi";
import { SurveyFeedback } from "./useSurveyFeedback";
import { SurveyLoader } from "./useSurveyLoader";

export interface AnswerSaver {
  isSavingAnswer: boolean;
  selectOption: (questionId: number, selectedOption: number) => Promise<void>;
}

function restoreOption(
  answers: Record<number, number>,
  questionId: number,
  previousOption: number | undefined,
): Record<number, number> {
  const restored = { ...answers };
  if (previousOption === undefined) {
    delete restored[questionId];
  } else {
    restored[questionId] = previousOption;
  }
  return restored;
}

/** Guarda cada respuesta en el borrador (CT-06) y la revierte si el guardado falla. */
export function useAnswerSaver(
  api: SurveyApiPort,
  loader: SurveyLoader,
  feedback: SurveyFeedback,
): AnswerSaver {
  const [isSavingAnswer, setIsSavingAnswer] = useState(false);
  const { draft, selectedOptionByQuestion } = loader.view;
  const { setSelectedMap } = loader;
  const { clearError, setSaveFeedback, showError } = feedback;

  const selectOption = useCallback(
    async (questionId: number, selectedOption: number) => {
      if (!draft) {
        return;
      }
      const previousOption = selectedOptionByQuestion[questionId];
      setSelectedMap((prev) => ({ ...prev, [questionId]: selectedOption }));
      setIsSavingAnswer(true);
      clearError();
      setSaveFeedback("Guardando respuesta...");
      try {
        await api.saveAnswer(draft.surveyId, { questionId, selectedOption });
        setSaveFeedback("Respuesta guardada en tu borrador.");
      } catch (error: unknown) {
        setSelectedMap((prev) => restoreOption(prev, questionId, previousOption));
        setSaveFeedback(null);
        showError(error);
      } finally {
        setIsSavingAnswer(false);
      }
    },
    [api, draft, selectedOptionByQuestion, setSelectedMap, clearError, setSaveFeedback, showError],
  );

  return { isSavingAnswer, selectOption };
}
