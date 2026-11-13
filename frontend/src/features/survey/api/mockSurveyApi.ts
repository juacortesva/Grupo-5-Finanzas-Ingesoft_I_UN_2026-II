import { ApiError } from "../../../api/httpClient";
import {
  AnswerDto,
  EvaluationResultResponse,
  EvaluationStatus,
  FinancialCategory,
  QuestionDto,
  SaveAnswerRequest,
  SurveyDraftResponse,
  SurveyStatus,
} from "../types";
import { SurveyApiPort } from "./surveyApi";

const MOCK_SURVEY_ID = "00000000-0000-4000-8000-000000000101";

const MOCK_QUESTIONS: QuestionDto[] = [
  {
    questionId: 1,
    text: "¿Cuántos meses de gastos básicos cubre actualmente tu fondo de emergencia?",
    displayOrder: 1,
    isRequired: true,
    options: [
      { selectedOption: 1, label: "Menos de 1 mes" },
      { selectedOption: 2, label: "Entre 1 y 3 meses" },
      { selectedOption: 3, label: "Más de 3 meses" },
    ],
  },
  {
    questionId: 2,
    text: "¿Qué porcentaje de tus ingresos mensuales destinas al ahorro o inversión?",
    displayOrder: 2,
    isRequired: true,
    options: [
      { selectedOption: 1, label: "Menos del 10%" },
      { selectedOption: 2, label: "Entre el 10% y el 20%" },
      { selectedOption: 3, label: "Más del 20%" },
    ],
  },
  {
    questionId: 3,
    text: "¿Cómo describirías tu nivel actual de deudas de consumo?",
    displayOrder: 3,
    isRequired: true,
    options: [
      { selectedOption: 1, label: "Alto (supera el 30% de mis ingresos)" },
      { selectedOption: 2, label: "Moderado y controlado" },
      { selectedOption: 3, label: "Sin deudas de consumo" },
    ],
  },
  {
    questionId: 4,
    text: "¿Cuál es el horizonte temporal de tu meta financiera principal?",
    displayOrder: 4,
    isRequired: true,
    options: [
      { selectedOption: 1, label: "Corto plazo (menos de 1 año)" },
      { selectedOption: 2, label: "Mediano plazo (1 a 5 años)" },
      { selectedOption: 3, label: "Largo plazo (más de 5 años)" },
    ],
  },
  {
    questionId: 5,
    text: "Si tu portafolio cayera un 15% temporalmente, ¿qué decisión tomarías?",
    displayOrder: 5,
    isRequired: true,
    options: [
      { selectedOption: 1, label: "Retiraría todo para evitar más pérdidas" },
      { selectedOption: 2, label: "Mantendría la inversión sin cambios" },
      { selectedOption: 3, label: "Aprovecharía para aportar más" },
    ],
  },
];

interface MockStoreState {
  surveyId: string;
  status: SurveyStatus;
  startedAt: string;
  answers: AnswerDto[];
  simulateEvaluationError: boolean;
}

function createInitialState(): MockStoreState {
  return {
    surveyId: MOCK_SURVEY_ID,
    status: SurveyStatus.DRAFT,
    startedAt: "2026-11-12T10:00:00Z",
    answers: [],
    simulateEvaluationError: false,
  };
}

let store: MockStoreState = createInitialState();

/** Reinicia o preconfigura el estado simulado (útil en pruebas unitarias). */
export function resetMockSurveyState(partial?: Partial<MockStoreState>): void {
  store = { ...createInitialState(), ...partial };
}

function resolveMockCategory(answers: AnswerDto[]): {
  category: FinancialCategory;
  score: string;
} {
  const optionSum = answers.reduce((acc, item) => acc + item.selectedOption, 0);
  if (optionSum <= 7) {
    return { category: FinancialCategory.CONSERVATIVE, score: "35.00" };
  }
  if (optionSum <= 11) {
    return { category: FinancialCategory.MODERATE, score: "65.00" };
  }
  return { category: FinancialCategory.AGGRESSIVE, score: "90.00" };
}

/** Adaptador simulado fiel a CT-01, CT-06 y CT-09 para desarrollo independiente. */
export const mockSurveyApi: SurveyApiPort = {
  async startSurvey(): Promise<SurveyDraftResponse> {
    if (store.status === SurveyStatus.COMPLETED) {
      store = createInitialState();
    }
    return {
      surveyId: store.surveyId,
      status: store.status,
      startedAt: store.startedAt,
      questions: MOCK_QUESTIONS,
      answers: [...store.answers],
    };
  },

  async saveAnswer(surveyId: string, payload: SaveAnswerRequest): Promise<void> {
    if (surveyId !== store.surveyId) {
      throw new ApiError(404, "Encuesta no encontrada.");
    }
    if (store.status !== SurveyStatus.DRAFT) {
      throw new ApiError(409, "No se altera una encuesta cerrada.");
    }

    const question = MOCK_QUESTIONS.find((q) => q.questionId === payload.questionId);
    const validOption = question?.options.some(
      (opt) => opt.selectedOption === payload.selectedOption,
    );
    if (!question || !validOption) {
      throw new ApiError(422, "Pregunta u opción inválida.");
    }

    const remaining = store.answers.filter((a) => a.questionId !== payload.questionId);
    store.answers = [...remaining, { ...payload }];
  },

  async completeSurvey(surveyId: string): Promise<EvaluationResultResponse> {
    if (surveyId !== store.surveyId) {
      throw new ApiError(404, "Encuesta no encontrada.");
    }
    if (store.status !== SurveyStatus.DRAFT) {
      throw new ApiError(409, "La encuesta ya fue completada.");
    }

    const answeredIds = new Set(store.answers.map((a) => a.questionId));
    const missingRequired = MOCK_QUESTIONS.some(
      (q) => q.isRequired && !answeredIds.has(q.questionId),
    );
    if (missingRequired) {
      throw new ApiError(422, "Faltan respuestas obligatorias por completar.");
    }

    store.status = SurveyStatus.COMPLETED;

    if (store.simulateEvaluationError) {
      return {
        surveyId: store.surveyId,
        assignedCategory: FinancialCategory.UNDER_EVALUATION,
        evaluationStatus: EvaluationStatus.ERROR,
        totalScore: null,
      };
    }

    const result = resolveMockCategory(store.answers);
    return {
      surveyId: store.surveyId,
      assignedCategory: result.category,
      evaluationStatus: EvaluationStatus.COMPLETED,
      totalScore: result.score,
    };
  },
};
