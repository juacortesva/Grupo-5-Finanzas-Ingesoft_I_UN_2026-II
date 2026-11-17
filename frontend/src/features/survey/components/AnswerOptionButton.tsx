import { AnswerOptionDto } from "../types";

interface AnswerOptionButtonProps {
  option: AnswerOptionDto;
  isSelected: boolean;
  isSaving: boolean;
  onSelect: (selectedOption: number) => void;
}

/** Opción de respuesta seleccionable, con semántica de radio para accesibilidad. */
export function AnswerOptionButton({
  option,
  isSelected,
  isSaving,
  onSelect,
}: AnswerOptionButtonProps) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={isSelected}
      disabled={isSaving}
      className={`option-button ${isSelected ? "option-button--selected" : ""}`}
      onClick={() => onSelect(option.selectedOption)}
    >
      <span className="option-indicator" aria-hidden="true" />
      <span>{option.label}</span>
    </button>
  );
}
