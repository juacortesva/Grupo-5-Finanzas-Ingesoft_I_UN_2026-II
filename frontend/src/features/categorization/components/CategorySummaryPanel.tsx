import { formatDecimalScore } from "../../../shared/utils/formatters";
import { CATEGORY_PRESENTATIONS } from "../types";
import { EvaluationResultResponse, EvaluationStatus } from "../../survey/types";

interface CategorySummaryPanelProps {
  result: EvaluationResultResponse;
}

export function CategorySummaryPanel({ result }: CategorySummaryPanelProps) {
  const presentation = CATEGORY_PRESENTATIONS[result.assignedCategory];
  const isProvisional = result.evaluationStatus === EvaluationStatus.ERROR;

  return (
    <div className="category-summary">
      <span className={`category-badge category-badge--${presentation.badgeTone}`}>
        {presentation.title}
      </span>

      <p className="category-description">{presentation.description}</p>

      {isProvisional ? (
        <div className="provisional-notice" role="status">
          No fue posible calcular tu puntaje definitivo en este intento, pero tu encuesta
          quedó registrada y puedes continuar hacia el panel principal.
        </div>
      ) : (
        <p className="category-score">
          Puntaje ponderado: <strong>{formatDecimalScore(result.totalScore)}</strong>
        </p>
      )}

      <ul className="plan-highlights">
        {presentation.planHighlights.map((highlight) => (
          <li key={highlight}>{highlight}</li>
        ))}
      </ul>
    </div>
  );
}
