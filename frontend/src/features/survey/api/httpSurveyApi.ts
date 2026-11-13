import { requestJson } from "../../../api/httpClient";
import {
  EvaluationResultResponse,
  SaveAnswerRequest,
  SurveyDraftResponse,
} from "../types";
import { SurveyApiPort } from "./surveyApi";

/** Adaptador HTTP real contra FastAPI para los contratos CT-01, CT-06 y CT-09. */
export const httpSurveyApi: SurveyApiPort = {
  async startSurvey(): Promise<SurveyDraftResponse> {
    return requestJson<SurveyDraftResponse>("/api/surveys", {
      method: "POST",
    });
  },

  async saveAnswer(surveyId: string, payload: SaveAnswerRequest): Promise<void> {
    await requestJson<void>(`/api/surveys/${surveyId}/answers`, {
      method: "PUT",
      body: payload,
    });
  },

  async completeSurvey(surveyId: string): Promise<EvaluationResultResponse> {
    return requestJson<EvaluationResultResponse>(`/api/surveys/${surveyId}/complete`, {
      method: "POST",
    });
  },
};
