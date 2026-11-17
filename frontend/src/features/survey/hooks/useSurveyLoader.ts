import { Dispatch, SetStateAction, useCallback, useEffect, useMemo, useState } from "react";
import { findNextPendingQuestionIndex } from "../../../shared/utils/formatters";
import { SurveyApiPort } from "../api/surveyApi";
import { QuestionDto, SurveyDraftResponse } from "../types";
import { SurveyFeedback } from "./useSurveyFeedback";

/** Estado del borrador visible para la vista. */
export interface SurveyDraftView {
  draft: SurveyDraftResponse | null;
  sortedQuestions: QuestionDto[];
  currentIndex: number;
  selectedOptionByQuestion: Readonly<Record<number, number>>;
  isLoading: boolean;
}

export interface SurveyLoader {
  view: SurveyDraftView;
  setSelectedMap: Dispatch<SetStateAction<Record<number, number>>>;
  setCurrentIndex: Dispatch<SetStateAction<number>>;
  loadSurvey: () => Promise<void>;
}

function sortQuestions(questions: QuestionDto[]): QuestionDto[] {
  return [...questions].sort((a, b) => a.displayOrder - b.displayOrder);
}

function buildAnswerMap(draft: SurveyDraftResponse): Record<number, number> {
  const map: Record<number, number> = {};
  for (const answer of draft.answers) {
    map[answer.questionId] = answer.selectedOption;
  }
  return map;
}

/** Inicia o reanuda el borrador (CT-01) y mantiene las respuestas y la pregunta actual. */
export function useSurveyLoader(api: SurveyApiPort, feedback: SurveyFeedback): SurveyLoader {
  const [draft, setDraft] = useState<SurveyDraftResponse | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOptionByQuestion, setSelectedMap] = useState<Record<number, number>>({});
  const [isLoading, setIsLoading] = useState(true);
  const { clearError, setSaveFeedback, showError } = feedback;

  const loadSurvey = useCallback(async () => {
    setIsLoading(true);
    clearError();
    setSaveFeedback(null);
    try {
      const loaded = await api.startSurvey();
      setDraft(loaded);
      setSelectedMap(buildAnswerMap(loaded));
      setCurrentIndex(
        findNextPendingQuestionIndex(sortQuestions(loaded.questions), loaded.answers),
      );
    } catch (error: unknown) {
      showError(error);
    } finally {
      setIsLoading(false);
    }
  }, [api, clearError, setSaveFeedback, showError]);

  useEffect(() => {
    void loadSurvey();
  }, [loadSurvey]);

  const sortedQuestions = useMemo(() => (draft ? sortQuestions(draft.questions) : []), [draft]);
  const view = { draft, sortedQuestions, currentIndex, selectedOptionByQuestion, isLoading };
  return { view, setSelectedMap, setCurrentIndex, loadSurvey };
}
