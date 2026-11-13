import { QuestionDto } from "../types";

interface QuestionCardProps {
  question: QuestionDto;
  selectedOption: number | undefined;
  isSaving: boolean;
  onSelectOption: (questionId: number, selectedOption: number) => void;
}

export function QuestionCard({
  question,
  selectedOption,
  isSaving,
  onSelectOption,
}: QuestionCardProps) {
  return (
    <section className="question-card" aria-labelledby={`question-${question.questionId}`}>
      <div className="question-header">
        <span className="question-badge">
          {question.isRequired ? "Obligatoria" : "Opcional"}
        </span>
      </div>

      <h2 id={`question-${question.questionId}`} className="question-title">
        {question.text}
      </h2>

      <div className="options-list" role="radiogroup" aria-label={question.text}>
        {question.options.map((option) => {
          const isSelected = selectedOption === option.selectedOption;
          return (
            <button
              key={option.selectedOption}
              type="button"
              role="radio"
              aria-checked={isSelected}
              disabled={isSaving}
              className={`option-button ${isSelected ? "option-button--selected" : ""}`}
              onClick={() => onSelectOption(question.questionId, option.selectedOption)}
            >
              <span className="option-indicator" aria-hidden="true" />
              <span>{option.label}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
