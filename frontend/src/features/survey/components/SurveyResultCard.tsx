import { CategorySummaryPanel } from "../../categorization/components/CategorySummaryPanel";
import { EvaluationResultResponse, EvaluationStatus } from "../types";

interface SurveyResultCardProps {
  result: EvaluationResultResponse;
  onRestart: () => void;
}

export function SurveyResultCard({ result, onRestart }: SurveyResultCardProps) {
  const isProvisional = result.evaluationStatus === EvaluationStatus.ERROR;

  return (
    <section className="result-card" aria-live="polite">
      <h2 className="result-title">
        {isProvisional
          ? "Encuesta completada con evaluación pendiente"
          : "¡Tu perfil financiero está listo!"}
      </h2>

      <CategorySummaryPanel result={result} />

      <div className="result-actions">
        <button type="button" className="secondary-button" onClick={onRestart}>
          Realizar nueva evaluación
        </button>
      </div>
    </section>
  );
}
