import { QuestionDto } from "../types";
import { AnswerOptionButton } from "./AnswerOptionButton";

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
        <span className="question-badge">{question.isRequired ? "Obligatoria" : "Opcional"}</span>
      </div>

      <h2 id={`question-${question.questionId}`} className="question-title">
        {question.text}
      </h2>

      <div className="options-list" role="radiogroup" aria-label={question.text}>
        {question.options.map((option) => (
          <AnswerOptionButton
            key={option.selectedOption}
            option={option}
            isSelected={selectedOption === option.selectedOption}
            isSaving={isSaving}
            onSelect={(chosen) => onSelectOption(question.questionId, chosen)}
          />
        ))}
      </div>
    </section>
  );
}
