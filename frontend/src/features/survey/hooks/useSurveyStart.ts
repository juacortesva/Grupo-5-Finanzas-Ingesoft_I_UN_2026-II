import { startSurvey, type SurveyStartResponse } from "../../../api/client";
import { type AsyncActionState, useAsyncAction } from "../../../shared/hooks/useAsyncAction";

export function useSurveyStart(): AsyncActionState<SurveyStartResponse> {
  return useAsyncAction(startSurvey);
}
