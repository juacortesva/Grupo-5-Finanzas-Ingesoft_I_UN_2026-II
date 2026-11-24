import { UseSurveyState } from "../hooks/useSurvey";

interface SurveyNavigationProps {
  survey: UseSurveyState;
}

interface PrimaryAction {
  label: string;
  disabled: boolean;
  onClick: () => void;
}

function resolvePrimaryAction(survey: UseSurveyState): PrimaryAction {
  const isLastQuestion = survey.currentIndex >= survey.sortedQuestions.length - 1;
  if (!isLastQuestion) {
    return {
      label: "Siguiente",
      disabled: survey.isSubmitting,
      onClick: survey.goToNextQuestion,
    };
  }
  return {
    label: survey.isSubmitting ? "Evaluando perfil..." : "Confirmar y enviar",
    disabled: !survey.allRequiredAnswered || survey.isSavingAnswer || survey.isSubmitting,
    onClick: () => void survey.submitSurvey(),
  };
}

/** Botones Anterior y Siguiente / Confirmar y enviar de la encuesta. */
export function SurveyNavigation({ survey }: SurveyNavigationProps) {
  const primaryAction = resolvePrimaryAction(survey);

  return (
    <div className="survey-navigation">
      <button
        type="button"
        className="secondary-button"
        disabled={survey.currentIndex === 0 || survey.isSubmitting}
        onClick={survey.goToPreviousQuestion}
      >
        Anterior
      </button>
      <button
        type="button"
        className="primary-button"
        disabled={primaryAction.disabled}
        onClick={primaryAction.onClick}
      >
        {primaryAction.label}
      </button>
    </div>
  );
}
