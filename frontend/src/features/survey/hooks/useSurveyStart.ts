import { startSurvey, type SurveyStartResponse } from "../../../api/client";
import type { AsyncActionState } from "../types";
import { useAsyncAction } from "./useAsyncAction";

/** Llama a POST /api/v1/surveys/start (contrato startSurvey, diseño 02 §3). */
export function useSurveyStart(): AsyncActionState<SurveyStartResponse> {
  return useAsyncAction(startSurvey);
}
