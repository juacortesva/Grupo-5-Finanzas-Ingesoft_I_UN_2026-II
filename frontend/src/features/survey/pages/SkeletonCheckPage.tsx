import type { ReactElement } from "react";

import { getApiUrl } from "../../../api/client";
import { useBackendHealth } from "../hooks/useBackendHealth";
import { useSurveyStart } from "../hooks/useSurveyStart";

/** Pantalla de texto plano para verificar React -> FastAPI -> PostgreSQL. */
export function SkeletonCheckPage(): ReactElement {
  const health = useBackendHealth();
  const survey = useSurveyStart();

  return (
    <main>
      <h1>Walking Skeleton</h1>
      <p>Backend: {getApiUrl()}</p>

      <button type="button" onClick={() => void health.run()} disabled={health.loading}>
        GET /api/v1/health
      </button>
      <pre>{health.error ?? JSON.stringify(health.data, null, 2)}</pre>

      <button type="button" onClick={() => void survey.run()} disabled={survey.loading}>
        POST /api/v1/surveys/start
      </button>
      <pre>{survey.error ?? JSON.stringify(survey.data, null, 2)}</pre>

      {survey.data !== null && (
        <p>
          surveyId={survey.data.surveyId} status={survey.data.status} preguntas=
          {survey.data.questions.length}
        </p>
      )}
    </main>
  );
}
