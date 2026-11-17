import { UseSurveyState } from "../hooks/useSurvey";
import { QuestionDto } from "../types";
import { QuestionCard } from "./QuestionCard";
import { SurveyNavigation } from "./SurveyNavigation";
import { SurveyProgressBar } from "./SurveyProgressBar";

interface SurveyQuestionStepProps {
  survey: UseSurveyState;
  question: QuestionDto;
}

/** Paso de la encuesta: progreso, pregunta actual, aviso de guardado y navegación. */
export function SurveyQuestionStep({ survey, question }: SurveyQuestionStepProps) {
  const { sortedQuestions, currentIndex, selectedOptionByQuestion } = survey;

  return (
    <>
      <SurveyProgressBar
        currentStep={currentIndex + 1}
        totalSteps={sortedQuestions.length}
        answeredCount={Object.keys(selectedOptionByQuestion).length}
      />
      <QuestionCard
        question={question}
        selectedOption={selectedOptionByQuestion[question.questionId]}
        isSaving={survey.isSavingAnswer || survey.isSubmitting}
        onSelectOption={(questionId, option) => void survey.selectOption(questionId, option)}
      />
      {survey.saveFeedback !== null && (
        <p className="save-feedback" role="status">
          {survey.saveFeedback}
        </p>
      )}
      <SurveyNavigation survey={survey} />
    </>
  );
}
