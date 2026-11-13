import { isMockApiEnabled } from "../../../api/healthService";
import {
  EvaluationResultResponse,
  SaveAnswerRequest,
  SurveyDraftResponse,
} from "../types";
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

export const surveyApi: SurveyApiPort = createSurveyApi();
