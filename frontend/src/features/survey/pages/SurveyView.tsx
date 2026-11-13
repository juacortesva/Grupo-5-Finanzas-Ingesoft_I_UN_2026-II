import { ErrorAlert } from "../../../shared/components/ErrorAlert";
import { QuestionCard } from "../components/QuestionCard";
import { SurveyProgressBar } from "../components/SurveyProgressBar";
import { SurveyResultCard } from "../components/SurveyResultCard";
import { useSurvey } from "../hooks/useSurvey";

export function SurveyView() {
  const {
    sortedQuestions,
    currentIndex,
    currentQuestion,
    selectedOptionByQuestion,
    isLoading,
    isSavingAnswer,
    isSubmitting,
    saveFeedback,
    errorMessage,
    result,
    allRequiredAnswered,
    selectOption,
    goToPreviousQuestion,
    goToNextQuestion,
    submitSurvey,
    restartSurvey,
  } = useSurvey();

  if (isLoading) {
    return (
      <section className="survey-card" aria-busy="true">
        <p className="status-text">Cargando tu cuestionario financiero...</p>
      </section>
    );
  }

  if (result !== null) {
    return (
      <SurveyResultCard
        result={result}
        onRestart={() => void restartSurvey()}
      />
    );
  }

  const answeredCount = Object.keys(selectedOptionByQuestion).length;
  const isFirstQuestion = currentIndex === 0;
  const isLastQuestion = currentIndex >= sortedQuestions.length - 1;

  return (
    <section className="survey-card">
      {errorMessage !== null && <ErrorAlert message={errorMessage} />}

      {sortedQuestions.length > 0 && currentQuestion !== null ? (
        <>
          <SurveyProgressBar
            currentStep={currentIndex + 1}
            totalSteps={sortedQuestions.length}
            answeredCount={answeredCount}
          />

          <QuestionCard
            question={currentQuestion}
            selectedOption={selectedOptionByQuestion[currentQuestion.questionId]}
            isSaving={isSavingAnswer || isSubmitting}
            onSelectOption={(questionId, selectedOption) =>
              void selectOption(questionId, selectedOption)
            }
          />

          {saveFeedback !== null && (
            <p className="save-feedback" role="status">
              {saveFeedback}
            </p>
          )}

          <div className="survey-navigation">
            <button
              type="button"
              className="secondary-button"
              disabled={isFirstQuestion || isSubmitting}
              onClick={goToPreviousQuestion}
            >
              Anterior
            </button>

            {isLastQuestion ? (
              <button
                type="button"
                className="primary-button"
                disabled={!allRequiredAnswered || isSavingAnswer || isSubmitting}
                onClick={() => void submitSurvey()}
              >
                {isSubmitting ? "Evaluando perfil..." : "Confirmar y enviar"}
              </button>
            ) : (
              <button
                type="button"
                className="primary-button"
                disabled={isSubmitting}
                onClick={goToNextQuestion}
              >
                Siguiente
              </button>
            )}
          </div>
        </>
      ) : (
        <p className="status-text">No hay preguntas activas disponibles en este momento.</p>
      )}
    </section>
  );
}
