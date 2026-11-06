# Guía de Estilo de Código y Convenciones — Asesor Financiero Personal

| | |
| :--- | :--- |
| **Equipo** | Grupo 5 (`@KevinVerjan`, `@Estebandido-exe`, `@josuarezvi`, `@juacortesva`) |
| **Stack Cubierto** | Python 3.11+ (FastAPI / SQLAlchemy / Pydantic), TypeScript 5+ (React / Vite), PostgreSQL |
| **Referencias** | `docs/adr/ADR-0001.md`, `docs/req/REQ-01.md`, `docs/design/01_Architectural_and_Detailed_Design.md`, `docs/design/02_Interaction_and_Data_Design.md` |

---

## 1. Filosofía General

1. **Automatización sobre discusión:** El formato del código no se discute en los *Pull Requests*. Si pasa el linter y el formateador automático (`Ruff` en Python, `ESLint + Prettier` en TypeScript), el formato es válido.
2. **Código en inglés, dominio claro:** Todo el código fuente (identificadores, clases, funciones, variables, tablas y columnas) se escribe en **inglés** para mantener consistencia con los diagramas de clases y de datos (`SurveyManager`, `evaluateProfile`, `assigned_category`). Los mensajes de error orientados al usuario final, los textos de la interfaz gráfica y la documentación de negocio/comentarios explicativos pueden ir en **español**.
3. **Tipado estricto de punta a punta:** Ninguna función se escribe sin tipos explícitos en su firma, ni en Python ni en TypeScript.

---

## 2. Convenciones de Nombres (Naming Case)

Adoptamos **estilo idiomático por lenguaje** con conversión automática en la frontera HTTP (Pydantic `alias_generator`). Esto respeta PEP 8 en Python, las convenciones de React/TypeScript y la correspondencia con los diagramas UML de las entregas de diseño.

### 2.1 Matriz de Nombres por Tecnología

| Elemento | Python (Backend) | TypeScript / React (Frontend) | PostgreSQL (Base de Datos) | JSON (Contrato API) |
| :--- | :--- | :--- | :--- | :--- |
| **Variables y funciones/métodos** | `snake_case` (`evaluate_profile`, `user_id`) | `camelCase` (`evaluateProfile`, `userId`) | N/A | `camelCase` (`surveyId`, `totalScore`) |
| **Clases, Modelos, Componentes UI** | `PascalCase` (`SurveyManager`, `ScoringEngine`) | `PascalCase` (`SurveyForm`, `EvaluationCard`) | N/A | N/A |
| **Interfaces y Tipos / Schemas** | `PascalCase` (`EvaluationResult`, `ProfileRepository`) | `PascalCase` (`EvaluationResult`, `SurveyDraft`) | N/A | N/A |
| **Constantes y Enumeraciones** | `UPPER_SNAKE_CASE` (`UNDER_EVALUATION`, `MAX_QUESTIONS`) | `UPPER_SNAKE_CASE` (`UNDER_EVALUATION`, `API_TIMEOUT`) | Valores en `UPPER_SNAKE_CASE` (`'DRAFT'`, `'COMPLETED'`) | `'UNDER_EVALUATION'` |
| **Tablas y Columnas** | Atributos SQLAlchemy en `snake_case` (`client_id`) | N/A | `snake_case` (`financial_profile`, `total_score`) | N/A |
| **Archivos y Módulos** | `snake_case.py` (`scoring_engine.py`) | Componentes: `PascalCase.tsx` (`SurveyView.tsx`)<br>Hooks/Utils: `camelCase.ts` (`useSurvey.ts`) | Migraciones en `snake_case.sql` | N/A |

### 2.2 Equivalencia entre Diagramas UML y Código Python

En los documentos de diseño (`01_Architectural_and_Detailed_Design.md` y `02_Interaction_and_Data_Design.md`), las operaciones están expresadas en `camelCase` estándar de UML. En Python se traducen directamente a `snake_case`:

* UML `evaluateProfile(userId, surveyId, answers)` $\rightarrow$ Python `evaluate_profile(self, user_id: UUID, survey_id: UUID, answers: list[Answer])`
* UML `calculateScore(answers)` $\rightarrow$ Python `calculate_score(self, answers: list[Answer])`
* UML `determineCategory(score)` $\rightarrow$ Python `determine_category(self, score: Decimal)`
* UML `findDraftByUserId(userId)` $\rightarrow$ Python `find_draft_by_user_id(self, user_id: UUID)`

### 2.3 Ejemplos de Nombres (Buenos vs. Malos)

```python
# ❌ MAL: Mezcla de español/inglés, abreviaturas crípticas y camelCase en Python
def calcPuntaje(usrId: UUID, rtas: list):
    totScore = 0.0
    return totScore

# ✅ BIEN: Inglés claro, snake_case idiomático y tipos explícitos del dominio
def calculate_score(self, answers: list[Answer]) -> Decimal:
    total_score = Decimal("0.00")
    return total_score
```

---

## 3. Reglas de Formato y Estructura de Funciones

### 3.1 Límites Cuantitativos

| Métrica | Límite | Justificación |
| :--- | :--- | :--- |
| **Longitud máxima de línea** | **88 caracteres** (Python) / **100 caracteres** (TS) | Evita desplazamiento horizontal y acomoda firmas con Type Hints sin cortar líneas prematuramente. |
| **Longitud máxima de función/método** | **35 líneas efectivas** (sin contar docstring) | Suficiente para expresar un flujo completo con manejo de errores (`evaluate_profile`), obligando a extraer submétodos si crece más. |
| **Parámetros por función** | **Máximo 4 parámetros** | Si una función requiere más de 4 parámetros, deben agruparse en un DTO/Schema de Pydantic o `@dataclass`. |
| **Complejidad ciclomática** | **Máximo 10** (`Ruff C901`) | Reduce la cantidad de caminos posibles y facilita alcanzar cobertura en pruebas unitarias con `pytest`. |
| **Niveles de indentación (anidamiento)** | **Máximo 3 niveles** | Se debe usar *Early Return* (cláusulas de guarda) en lugar de bloques `if/else` profundamente anidados. |

### 3.2 Cláusulas de Guarda (Early Return) vs. Anidamiento

```python
# ❌ MAL: Anidamiento excesivo (Arrow Anti-pattern)
def save_draft(self, survey_id: UUID, user_id: UUID, answers: list[Answer]) -> None:
    survey = self._survey_repo.find_by_id(survey_id, user_id)
    if survey is not None:
        if survey.status == SurveyStatus.DRAFT:
            survey.update_answers(answers)
            self._survey_repo.save(survey)
        else:
            raise SurveyAlreadyCompletedError("No se altera una encuesta cerrada.")
    else:
        raise SurveyNotFoundError("Encuesta no encontrada.")

# ✅ BIEN: Cláusulas de guarda planas y legibles
def save_draft(self, survey_id: UUID, user_id: UUID, answers: list[Answer]) -> None:
    survey = self._survey_repo.find_by_id(survey_id, user_id)
    if survey is None:
        raise SurveyNotFoundError("Encuesta no encontrada.")
    if survey.status != SurveyStatus.DRAFT:
        raise SurveyAlreadyCompletedError("No se altera una encuesta cerrada.")

    survey.update_answers(answers)
    self._survey_repo.save(survey)
```

---

## 4. Precisión Numérica y Reglas Financieras (`ADR-0001`)

De acuerdo con `ADR-0001` y la sección 2.4 de `02_Interaction_and_Data_Design.md`, **está terminantemente prohibido el uso de `float`** para puntajes, pesos de preguntas, opciones de respuesta o montos financieros.

### 4.1 Reglas de `Decimal` en Python

1. **Inicialización siempre desde `str` o `int`**, nunca desde un literal `float`.
2. **Cuantización explícita** cuando se requiera redondeo, definiendo la estrategia de redondeo del módulo `decimal`.
3. En SQLAlchemy, usar siempre `Numeric(precision, scale)` con `asdecimal=True`.

```python
from decimal import Decimal

# ❌ MAL: Inicializar Decimal con float hereda la imprecisión IEEE 754
weight = Decimal(0.15)  # Produce Decimal('0.1499999999999999944488848768742172978818416595458984375')
score: float = 10.5 * 0.15

# ✅ BIEN: Inicialización exacta desde string
weight = Decimal("0.15")
option_value = Decimal("10.50")
score: Decimal = option_value * weight
```

---

## 5. Documentación en Código y Comentarios

### 5.1 Principio Rector: Explicar el "Por Qué" y la Trazabilidad, no el "Qué"

* **Prohibido comentar qué hace el código** si ya es evidente al leer el nombre de la función o variable.
* **Prohibido dejar código comentado** en la rama principal (para eso existe el historial de Git).
* **Obligatorio referenciar Reglas de Negocio (`BR-01`, `BR-02`, `BR-03`), Requerimientos (`REQ-01`) o Decisiones (`ADR-0001`)** cuando una línea implemente una restricción específica del dominio.

### 5.2 Estándar de Docstrings (Formato Google en Python)

Los *docstrings* son **obligatorios** en:
1. Clases de servicio y motores de dominio (`SurveyManager`, `CategorizationService`, `ScoringEngine`).
2. Interfaces de repositorios (`SurveyRepository`, `ProfileRepository`).
3. Métodos públicos que implementan contratos de diseño.

No se requieren *docstrings* en funciones privadas triviales, getters o setters simples.

```python
# ❌ MAL: Comentarios redundantes que repiten el código y sin trazabilidad
class ScoringEngine:
    # Esta función determina la categoría
    def determine_category(self, score: Decimal) -> FinancialCategory:
        # Si el score es menor o igual al límite conservador
        if score <= self._conservative_upper_limit:
            return FinancialCategory.CONSERVATIVE # Retorna conservador
        return FinancialCategory.MODERATE

# ✅ BIEN: Docstring conciso con contrato y comentario trazable a la regla de negocio
class ScoringEngine:
    def determine_category(self, score: Decimal) -> FinancialCategory:
        """Determina la categoría financiera inicial según el puntaje ponderado.

        Args:
            score: Puntaje total calculado con precisión Decimal.

        Returns:
            Categoría financiera asignada al perfil del cliente.
        """
        # BR-03 (REQ-01): En caso de ubicarse exactamente en el umbral (<=),
        # se asigna por defecto la categoría de menor riesgo (más conservadora).
        if score <= self._conservative_threshold:
            return FinancialCategory.CONSERVATIVE
        if score <= self._moderate_threshold:
            return FinancialCategory.MODERATE
        return FinancialCategory.AGGRESSIVE
```

---

## 6. Manejo de Errores, Excepciones y Privacidad en Logs

Siguiendo la sección 3.4 de `01_Architectural_and_Detailed_Design.md` y la mitigación de riesgos de `REQ-01`:

1. **Excepciones de Dominio Personalizadas:** Los servicios y motores de negocio lanzan excepciones semánticas (`InvalidInputError`, `SurveyNotFoundError`, `SurveyAlreadyCompletedError`), **nunca** `HTTPException` de FastAPI directamente (eso pertenece exclusivamente a la capa `router`).
2. **Privacidad en Logs (Regla de Seguridad `REQ-01`):** Está prohibido registrar en los logs (`logger.error`, `print`) las respuestas del cliente (`answers`), los puntajes obtenidos (`total_score`) o datos personales/financieros. Solo se registra el tipo de error técnico, el nombre de la operación y la marca de tiempo.

```python
# ❌ MAL: Filtra datos financieros sensibles del usuario en los logs y acopla el servicio a HTTP
except Exception as err:
    logger.error(f"Error evaluando usuario {user_id} con respuestas {answers} y score {total_score}: {err}")
    raise HTTPException(status_code=500, detail="Error interno")

# ✅ BIEN: Cumple REQ-01 Escenario 3 y protege la privacidad del cliente en logs
except Exception as err:
    # REQ-01 Mitigación de Riesgo: No incluir respuestas, puntajes ni PII en logs.
    logger.error(
        "Evaluation failed during profile categorization",
        extra={
            "error_type": type(err).__name__,
            "operation": "evaluate_profile",
        },
    )
    provisional_category = FinancialCategory.UNDER_EVALUATION
    self._profile_repo.save_category(
        user_id=user_id,
        survey_id=survey_id,
        category=provisional_category,
        status=EvaluationStatus.ERROR,
    )
    return EvaluationResult(
        survey_id=survey_id,
        assigned_category=provisional_category,
        total_score=None,
        status=EvaluationStatus.ERROR,
    )
```

---

## 7. Estilo Específico para Frontend (React + TypeScript)

1. **Prohibido el tipo `any`:** Si un tipo es dinámico o desconocido antes de validarse, se utiliza `unknown` con *type guards*.
2. **Componentes Funcionales Tipados:** Declarar componentes con funciones explícitas e interfaces para sus `Props`. Un solo componente principal exportado por archivo `.tsx`.
3. **Separación de Lógica y Vista:** Los componentes `.tsx` solo se encargan de renderizar y capturar interacciones del usuario. Las llamadas HTTP a los endpoints de FastAPI y la gestión de estado viven en *Custom Hooks* (`useSurveyDraft`, `useEvaluateProfile`) o servicios de la capa `api/`.
4. **Serialización de `Decimal` en Frontend:** Los valores `Decimal` enviados desde FastAPI se manejan en TypeScript como `string` para visualización o mediante utilidades dedicadas de formato numérico, evitando aritmetizar con `number` nativo en el cliente si afecta precisión.

```tsx
// ❌ MAL: Uso de any, fetch directo en el render y nombres ambiguos
export const SurveyComp = (props: any) => {
  const send = async () => {
    const res = await fetch("/api/surveys/" + props.id + "/complete");
  };
  return <button onClick={send}>Enviar</button>;
};

// ✅ BIEN: Props tipadas, nombres expresivos y delegación de lógica a hooks
interface SurveySubmitButtonProps {
  surveyId: string;
  isComplete: boolean;
  onCompleteSurvey: (surveyId: string) => Promise<void>;
}

export function SurveySubmitButton({
  surveyId,
  isComplete,
  onCompleteSurvey,
}: SurveySubmitButtonProps) {
  return (
    <button
      type="button"
      disabled={!isComplete}
      onClick={() => void onCompleteSurvey(surveyId)}
    >
      Confirmar envío de encuesta
    </button>
  );
}
```

---

## 8. Estilo de Pruebas Automatizadas (`pytest` / `Vitest`)

1. **Nomenclatura de funciones de prueba:** Usar el patrón `test_<operacion>_when_<condicion>_then_<resultado_esperado>` para que el reporte de pruebas sea autoexplicativo.
2. **Estructura AAA (Arrange - Act - Assert):** Toda prueba unitaria o de integración debe separar visualmente (con una línea en blanco) la preparación de datos, la ejecución de la operación y la verificación del resultado.

```python
def test_determine_category_when_score_is_on_exact_threshold_then_assigns_lower_risk() -> None:
    # Arrange (BR-03: umbral exacto en 50.00 entre CONSERVATIVE y MODERATE)
    engine = ScoringEngine(conservative_threshold=Decimal("50.00"), moderate_threshold=Decimal("80.00"))
    boundary_score = Decimal("50.00")

    # Act
    category = engine.determine_category(boundary_score)

    # Assert
    assert category == FinancialCategory.CONSERVATIVE
```

---

## 9. Configuración Base de Herramientas (Copia y Pega)

### 9.1 Python (`backend/pyproject.toml`)

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (orden automático de imports)
    "N",   # pep8-naming (valida snake_case y PascalCase)
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C90", # mccabe (complejidad ciclomática)
]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.mypy]
python_version = "3.11"
strict = true
disallow_untyped_defs = true
no_implicit_optional = true
```

### 9.2 Esquema Base Pydantic con Conversión Automática `snake_case` $\leftrightarrow$ `camelCase`

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelCaseSchema(BaseModel):
    """Clase base para todos los DTOs expuestos en la API REST."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
```
