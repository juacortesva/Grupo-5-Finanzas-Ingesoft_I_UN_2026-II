# CT-10 — `CategorizationService.evaluateProfile`

| | |
|---|---|
| **Versión** | 1.1 (2026-11-12) — incorpora hallazgos F-01…F-21 de la auditoría de contratos |
| **Estado** | Propuesto |
| **Trazabilidad** | `REQ-01` · AC-01.1, AC-01.3 · `BR-04`, `BR-05`, `BR-06` · NFR de precisión numérica y de privacidad · `02` §1.1 (`evaluateProfile`), §3.1 (contrato detallado) · `01` §3.2 (Diagrama A), §3.4 (pseudocódigo) · `ADR-0001` |
| **Contratos relacionados** | Lo invoca CT-09; usa CT-11 (`ScoringEngine`) y CT-12 (`saveCategory`) |

## 1. Descripción y características del contrato

* **Componentes involucrados:** Solicita `SurveyManager` (Módulo `survey`) y provee `CategorizationService` (Módulo `categorization`; en Python, `evaluate_profile(self, user_id: UUID, survey_id: UUID, answers: list[ScoredAnswerDTO]) -> EvaluationResult`). La comunicación entre módulos usa solo DTOs de `categorization/schemas.py` (ley de frontera, `docs/estructura_repositorio.md` §4.2).
* **Precondiciones (garantiza el solicitante):**
  * `SurveyManager` ya validó propiedad, estado `DRAFT` y respuestas obligatorias, y **confirmó** el cierre de `surveyId` en `COMPLETED` (`BR-03`).
  * `userId` es el dueño de `surveyId`.
  * `answers` se construyó desde las respuestas persistidas, con `optionValue` y `weight` como `Decimal` (`ADR-0001`).
* **Validación defensiva del proveedor:** Si `answers` está vacía, lanza `InvalidInputError` **sin** llamar a `saveCategory` (`02` §3.1).
* **Postcondiciones (garantiza el proveedor):**
  * **Éxito:** obtiene `totalScore = ScoringEngine.calculateScore(answers)` y `assignedCategory = ScoringEngine.determineCategory(totalScore)` (CT-11, aplica `BR-05`). Persiste con `ProfileRepository.saveCategory(userId, ProfileEvaluation(surveyId, assignedCategory, COMPLETED, totalScore))` (CT-12) y retorna `EvaluationResult(surveyId, assignedCategory, COMPLETED, totalScore)`.
  * **Fallo del motor o de la persistencia definitiva (`BR-06`):** registra `logError(errorType, operation, timestamp)`, persiste `ProfileEvaluation(surveyId, UNDER_EVALUATION, ERROR, null)` y retorna `EvaluationResult(surveyId, UNDER_EVALUATION, ERROR, null)`.
  * **Fallo doble:** si también falla la persistencia provisional, lanza `EvaluationPersistenceError`; en ese caso no se garantiza que el perfil exista o esté actualizado.
* **Invariantes:**
  * Coherencia (`BR-06`): `evaluationStatus = ERROR` ⇔ `assignedCategory = UNDER_EVALUATION` ⇔ `totalScore = null`. `evaluationStatus = COMPLETED` ⇒ `assignedCategory` ∈ {`CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`} y `totalScore ≠ null`.
  * Tras un éxito o un fallo con perfil provisional, existe **exactamente un** perfil vigente para `userId`, vinculado a `surveyId` (`BR-04`), y coincide con el `EvaluationResult` devuelto.
  * No modifica la encuesta ni sus respuestas (`BR-03`).
  * Privacidad: `logError` recibe solo el tipo de error, la operación y la marca de tiempo; **nunca** respuestas, puntajes ni PII.
  * Sin reintentos en segundo plano (`ADR-0001` rechazó brokers; `02` §5).
* **Efectos secundarios:** Crea o actualiza (upsert) el único perfil financiero vigente del cliente.

## 2. Resultados de fallo

| Condición | Resultado | Estado resultante |
|---|---|---|
| `answers` vacía | `InvalidInputError` | Perfil intacto; no se llama a `saveCategory` |
| Excepción en `calculateScore` o `determineCategory` | `EvaluationResult(UNDER_EVALUATION, ERROR, null)` | Perfil provisional persistido (`BR-06`) |
| Excepción en `saveCategory` definitivo | `EvaluationResult(UNDER_EVALUATION, ERROR, null)` | Perfil provisional persistido (`BR-06`) |
| También falla `saveCategory` provisional | `EvaluationPersistenceError` | Perfil no garantizado; la encuesta sigue `COMPLETED` |

## 3. Estructura esencial (`.json`)

```json
{
  "input": {
    "userId": "UUID (requerido)",
    "surveyId": "UUID (requerido; encuesta ya cerrada en COMPLETED)",
    "answers": [
      {
        "questionId": "int (requerido)",
        "optionValue": "Decimal (requerido)",
        "weight": "Decimal >= 0 (requerido; de question.weight)"
      }
    ]
  },
  "output": {
    "surveyId": "UUID (requerido)",
    "assignedCategory": "FinancialCategory (requerido; CONSERVATIVE | MODERATE | AGGRESSIVE | UNDER_EVALUATION)",
    "evaluationStatus": "EvaluationStatus (requerido; COMPLETED | ERROR)",
    "totalScore": "Decimal | null (null si y solo si evaluationStatus = ERROR)"
  }
}
```

## 4. Ejemplos verificables

| Caso | Antes | Invocación | Resultado esperado |
|---|---|---|---|
| Éxito (Escenario 1) | Encuesta `S1` `COMPLETED` | `evaluateProfile(U1, S1, answers[n])` con puntaje dentro de una banda | `(S1, <banda>, COMPLETED, totalScore)`; un perfil para `U1` con `survey_id = S1` |
| Empate en umbral (`BR-05`) | Ídem | Puntaje igual al límite entre `CONSERVATIVE` y `MODERATE` | `assignedCategory = CONSERVATIVE` |
| Fallo del motor (Escenario 3) | Ídem; `calculateScore` lanza una excepción | `evaluateProfile(U1, S1, answers)` | `(S1, UNDER_EVALUATION, ERROR, null)`; perfil provisional; log sin PII |
| Entrada vacía | Cualquiera | `evaluateProfile(U1, S1, [])` | `InvalidInputError`; perfil intacto |
| Reevaluación | Perfil vigente de `S0` | `evaluateProfile(U1, S2, answers')` | Un solo perfil para `U1`, ahora con `survey_id = S2` |

## 5. Notas de alineación con `01`

* `01` §3.2 declara `evaluateProfile(userId, surveyId, answers : List~Answer~)`; debería recibir `List~ScoredAnswerDTO~`, que lleva el `weight`, para no acoplar el Módulo `categorization` a la entidad `Answer` del Módulo `survey`.
