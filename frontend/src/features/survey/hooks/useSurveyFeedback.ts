import { useCallback, useState } from "react";
import { ApiError } from "../../../api/httpClient";

/** Mensajes visibles para el usuario, compartidos por los hooks de la encuesta. */
export interface SurveyFeedback {
  errorMessage: string | null;
  saveFeedback: string | null;
  showError: (error: unknown) => void;
  clearError: () => void;
  setSaveFeedback: (message: string | null) => void;
}

function resolveUserErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  return "Ocurrió un error inesperado. Por favor, intenta nuevamente.";
}

/** Estado del mensaje de error y del aviso de guardado de la encuesta. */
export function useSurveyFeedback(): SurveyFeedback {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [saveFeedback, setSaveFeedback] = useState<string | null>(null);

  const showError = useCallback((error: unknown) => {
    setErrorMessage(resolveUserErrorMessage(error));
  }, []);

  const clearError = useCallback(() => {
    setErrorMessage(null);
  }, []);

  return { errorMessage, saveFeedback, showError, clearError, setSaveFeedback };
}
