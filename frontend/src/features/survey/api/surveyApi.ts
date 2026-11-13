import { isMockApiEnabled } from "../../../api/healthService";
import { EvaluationResultResponse, SaveAnswerRequest, SurveyDraftResponse } from "../types";
import { httpSurveyApi } from "./httpSurveyApi";
import { mockSurveyApi } from "./mockSurveyApi";

/** Puerto de acceso a operaciones de encuesta desacoplado de transporte HTTP o mocks. */
export interface SurveyApiPort {
  startSurvey(): Promise<SurveyDraftResponse>;
  saveAnswer(surveyId: string, payload: SaveAnswerRequest): Promise<void>;
  completeSurvey(surveyId: string): Promise<EvaluationResultResponse>;
}

export function createSurveyApi(useMock = isMockApiEnabled()): SurveyApiPort {
  return useMock ? mockSurveyApi : httpSurveyApi;
}

/**
 * Adaptador activo por defecto: usa HTTP real contra FastAPI salvo que
 * VITE_USE_MOCK_API === "true" esté habilitado explícitamente.
 */
export const surveyApi: SurveyApiPort = {
  startSurvey() {
    return createSurveyApi().startSurvey();
  },
  saveAnswer(surveyId, payload) {
    return createSurveyApi().saveAnswer(surveyId, payload);
  },
  completeSurvey(surveyId) {
    return createSurveyApi().completeSurvey(surveyId);
  },
};
