import type { components } from "./generated/schema";

export type SurveyStartResponse = components["schemas"]["SurveyStartResponse"];
export type HealthResponse = Record<string, string>;

const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(`${API_URL}${path}`, init);
  const body: unknown = await response.json();
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${JSON.stringify(body)}`);
  }
  return body;
}

function isHealthResponse(value: unknown): value is HealthResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    Object.values(value).every((field) => typeof field === "string")
  );
}

function isSurveyStartResponse(value: unknown): value is SurveyStartResponse {
  return typeof value === "object" && value !== null && "surveyId" in value && "questions" in value;
}

export function getApiUrl(): string {
  return API_URL;
}

export async function getHealth(): Promise<HealthResponse> {
  const body = await request("/api/v1/health");
  if (!isHealthResponse(body)) {
    throw new Error("Respuesta inesperada de /health.");
  }
  return body;
}

export async function startSurvey(): Promise<SurveyStartResponse> {
  // El userId nunca va en el body (REQ-01): el backend lo toma de la cabecera
  // o, en modo demo del Walking Skeleton, usa el cliente demo.
  const body = await request("/api/v1/surveys/start", { method: "POST" });
  if (!isSurveyStartResponse(body)) {
    throw new Error("Respuesta inesperada de /surveys/start.");
  }
  return body;
}
