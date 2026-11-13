import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resetMockSurveyState } from "../api/mockSurveyApi";
import { SurveyView } from "./SurveyView";

describe("SurveyView", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_USE_MOCK_API", "true");
    resetMockSurveyState();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllEnvs();
  });

  it("test_survey_view_when_loaded_then_displays_question_and_saves_answer", async () => {
    // Arrange
    render(<SurveyView />);
    const firstOption = await screen.findByRole("radio", { name: "Más de 3 meses" });

    // Act
    fireEvent.click(firstOption);

    // Assert
    await waitFor(() => {
      expect(screen.getByText("Respuesta guardada en tu borrador.")).toBeInTheDocument();
    });
  });

  it("test_survey_view_when_all_questions_answered_then_completes_and_shows_category", async () => {
    // Arrange
    resetMockSurveyState({
      answers: [
        { questionId: 1, selectedOption: 2 },
        { questionId: 2, selectedOption: 2 },
        { questionId: 3, selectedOption: 2 },
        { questionId: 4, selectedOption: 2 },
      ],
    });
    render(<SurveyView />);
    const lastOption = await screen.findByRole("radio", {
      name: "Mantendría la inversión sin cambios",
    });

    // Act
    fireEvent.click(lastOption);
    const submitButton = await screen.findByRole("button", { name: "Confirmar y enviar" });
    await waitFor(() => expect(submitButton).not.toBeDisabled());
    fireEvent.click(submitButton);

    // Assert
    expect(await screen.findByText("¡Tu perfil financiero está listo!")).toBeInTheDocument();
    expect(screen.getByText("Perfil Moderado")).toBeInTheDocument();
  });
});
