import { ErrorAlert } from "../../../shared/components/ErrorAlert";
import { SurveyQuestionStep } from "../components/SurveyQuestionStep";
import { SurveyResultCard } from "../components/SurveyResultCard";
import { useSurvey } from "../hooks/useSurvey";

export function SurveyView() {
  const survey = useSurvey();

  if (survey.isLoading) {
    return (
      <section className="survey-card" aria-busy="true">
        <p className="status-text">Cargando tu cuestionario financiero...</p>
      </section>
    );
  }

  if (survey.result !== null) {
    return (
      <SurveyResultCard result={survey.result} onRestart={() => void survey.restartSurvey()} />
    );
  }

  return (
    <section className="survey-card">
      {survey.errorMessage !== null && <ErrorAlert message={survey.errorMessage} />}
      {survey.currentQuestion !== null ? (
        <SurveyQuestionStep survey={survey} question={survey.currentQuestion} />
      ) : (
        <p className="status-text">No hay preguntas activas disponibles en este momento.</p>
      )}
    </section>
  );
}
