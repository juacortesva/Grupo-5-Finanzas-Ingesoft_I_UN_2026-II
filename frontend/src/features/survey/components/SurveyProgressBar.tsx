interface SurveyProgressBarProps {
  currentStep: number;
  totalSteps: number;
  answeredCount: number;
}

export function SurveyProgressBar({
  currentStep,
  totalSteps,
  answeredCount,
}: SurveyProgressBarProps) {
  const percentage = totalSteps > 0 ? Math.round((answeredCount / totalSteps) * 100) : 0;

  return (
    <div className="progress-container">
      <div className="progress-labels">
        <span>
          Pregunta {currentStep} de {totalSteps}
        </span>
        <span>
          {answeredCount} respondida(s) ({percentage}%)
        </span>
      </div>
      <div
        className="progress-track"
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="progress-fill" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}
