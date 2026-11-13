import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError } from "../../../api/httpClient";
import { findNextPendingQuestionIndex } from "../../../shared/utils/formatters";
import { SurveyApiPort, surveyApi } from "../api/surveyApi";
import { EvaluationResultResponse, QuestionDto, SurveyDraftResponse } from "../types";

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

function buildAnswerMap(draft: SurveyDraftResponse): Record<number, number> {
  const map: Record<number, number> = {};
  for (const answer of draft.answers) {
    map[answer.questionId] = answer.selectedOption;
  }
  return map;
}

function resolveUserErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  return "Ocurrió un error inesperado. Por favor, intenta nuevamente.";
}

/** Custom hook que orquesta el ciclo de vida de la encuesta (CT-01, CT-06 y CT-09). */
export function useSurvey(api: SurveyApiPort = surveyApi): UseSurveyState {
  const [draft, setDraft] = useState<SurveyDraftResponse | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedMap, setSelectedMap] = useState<Record<number, number>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingAnswer, setIsSavingAnswer] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [saveFeedback, setSaveFeedback] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<EvaluationResultResponse | null>(null);

  const loadSurvey = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    setResult(null);
    setSaveFeedback(null);
    try {
      const loadedDraft = await api.startSurvey();
      const ordered = [...loadedDraft.questions].sort((a, b) => a.displayOrder - b.displayOrder);
      setDraft(loadedDraft);
      setSelectedMap(buildAnswerMap(loadedDraft));
      setCurrentIndex(findNextPendingQuestionIndex(ordered, loadedDraft.answers));
    } catch (error: unknown) {
      setErrorMessage(resolveUserErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void loadSurvey();
  }, [loadSurvey]);

  const sortedQuestions = useMemo(() => {
    if (!draft) {
      return [];
    }
    return [...draft.questions].sort((a, b) => a.displayOrder - b.displayOrder);
  }, [draft]);

  const currentQuestion = sortedQuestions[currentIndex] ?? null;

  const allRequiredAnswered = useMemo(() => {
    if (sortedQuestions.length === 0) {
      return false;
    }
    return sortedQuestions.every((q) => !q.isRequired || selectedMap[q.questionId] !== undefined);
  }, [sortedQuestions, selectedMap]);

  const selectOption = useCallback(
    async (questionId: number, selectedOption: number) => {
      if (!draft) {
        return;
      }
      const previousOption = selectedMap[questionId];
      setSelectedMap((prev) => ({ ...prev, [questionId]: selectedOption }));
      setIsSavingAnswer(true);
      setErrorMessage(null);
      setSaveFeedback("Guardando respuesta...");

      try {
        await api.saveAnswer(draft.surveyId, { questionId, selectedOption });
        setSaveFeedback("Respuesta guardada en tu borrador.");
      } catch (error: unknown) {
        setSelectedMap((prev) => {
          const restored = { ...prev };
          if (previousOption === undefined) {
            delete restored[questionId];
          } else {
            restored[questionId] = previousOption;
          }
          return restored;
        });
        setSaveFeedback(null);
        setErrorMessage(resolveUserErrorMessage(error));
      } finally {
        setIsSavingAnswer(false);
      }
    },
    [api, draft, selectedMap],
  );

  const goToPreviousQuestion = useCallback(() => {
    setCurrentIndex((prev) => Math.max(0, prev - 1));
    setSaveFeedback(null);
  }, []);

  const goToNextQuestion = useCallback(() => {
    setCurrentIndex((prev) => Math.min(sortedQuestions.length - 1, prev + 1));
    setSaveFeedback(null);
  }, [sortedQuestions.length]);

  const submitSurvey = useCallback(async () => {
    if (!draft) {
      return;
    }
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const evaluation = await api.completeSurvey(draft.surveyId);
      setResult(evaluation);
    } catch (error: unknown) {
      setErrorMessage(resolveUserErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }, [api, draft]);

  return {
    draft,
    sortedQuestions,
    currentIndex,
    currentQuestion,
    selectedOptionByQuestion: selectedMap,
    isLoading,
    isSavingAnswer,
    isSubmitting,
    saveFeedback,
    errorMessage,
    result,
    allRequiredAnswered,
    selectOption,
    goToPreviousQuestion,
    goToNextQuestion,
    submitSurvey,
    restartSurvey: loadSurvey,
  };
}
