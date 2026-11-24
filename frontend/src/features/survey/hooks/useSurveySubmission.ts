import { useCallback, useState } from "react";
import { SurveyApiPort } from "../api/surveyApi";
import { EvaluationResultResponse, SurveyDraftResponse } from "../types";
import { SurveyFeedback } from "./useSurveyFeedback";

export interface SurveySubmission {
  isSubmitting: boolean;
  result: EvaluationResultResponse | null;
  submitSurvey: () => Promise<void>;
  resetResult: () => void;
}

/** Completa la encuesta (CT-09) y conserva el resultado de la evaluación. */
export function useSurveySubmission(
  api: SurveyApiPort,
  draft: SurveyDraftResponse | null,
  feedback: SurveyFeedback,
): SurveySubmission {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<EvaluationResultResponse | null>(null);
  const { clearError, showError } = feedback;

  const submitSurvey = useCallback(async () => {
    if (!draft) {
      return;
    }
    setIsSubmitting(true);
    clearError();
    try {
      setResult(await api.completeSurvey(draft.surveyId));
    } catch (error: unknown) {
      showError(error);
    } finally {
      setIsSubmitting(false);
    }
  }, [api, draft, clearError, showError]);

  const resetResult = useCallback(() => {
    setResult(null);
  }, []);

  return { isSubmitting, result, submitSurvey, resetResult };
}
