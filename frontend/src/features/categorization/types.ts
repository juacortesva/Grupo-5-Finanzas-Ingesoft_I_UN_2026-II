import { FinancialCategory } from "../survey/types";

export interface CategoryPresentation {
  title: string;
  description: string;
  badgeTone: "conservative" | "moderate" | "aggressive" | "provisional";
  planHighlights: string[];
}

export const CATEGORY_PRESENTATIONS: Readonly<Record<FinancialCategory, CategoryPresentation>> =
  {
    [FinancialCategory.CONSERVATIVE]: {
      title: "Perfil Conservador",
      description:
        "Priorizas la estabilidad de tu capital y un fondo sólido antes de asumir riesgos.",
      badgeTone: "conservative",
      planHighlights: [
        "Meta inicial: fondo de liquidez equivalente a 3 a 6 meses de gastos.",
        "Instrumentos sugeridos: cuentas remuneradas y renta fija de bajo riesgo.",
      ],
    },
    [FinancialCategory.MODERATE]: {
      title: "Perfil Moderado",
      description:
        "Buscas un equilibrio entre protección financiera y crecimiento gradual a mediano plazo.",
      badgeTone: "moderate",
      planHighlights: [
        "Meta inicial: balance entre ahorro programado y diversificación controlada.",
        "Instrumentos sugeridos: combinación de renta fija y fondos diversificados.",
      ],
    },
    [FinancialCategory.AGGRESSIVE]: {
      title: "Perfil Crecimiento",
      description:
        "Tienes margen financiero y horizonte largo para buscar mayor rendimiento con volatilidad.",
      badgeTone: "aggressive",
      planHighlights: [
        "Meta inicial: maximizar aportes periódicos con horizonte de largo plazo.",
        "Instrumentos sugeridos: portafolio diversificado orientado a renta variable.",
      ],
    },
    [FinancialCategory.UNDER_EVALUATION]: {
      title: "En Evaluación (Provisional)",
      description:
        "Tu encuesta se guardó correctamente, pero ocurrió una falla temporal al evaluarla.",
      badgeTone: "provisional",
      planHighlights: [
        "Tus respuestas permanecen seguras y cerradas sin pérdida de información.",
        "Puedes continuar explorando la plataforma mientras se regulariza tu evaluación.",
      ],
    },
  };
