# CT-09 — `completeSurvey` (HTTP + `SurveyManager`)

| | |
|---|---|
| **Versión** | 1.1 (2026-11-12) — incorpora hallazgos F-01…F-21 de la auditoría de contratos |
| **Estado** | Propuesto |
| **Trazabilidad** | `REQ-01` · US-01 · AC-01.1, AC-01.3 · `BR-03`, `BR-04`, `BR-05`, `BR-06` · NFR de privacidad · `02` §1.1 (`completeSurvey`), §2.4, §3.2 (fila `completeSurvey`) · `01` §3.2 (`SurveyManager.completeSurvey`) |
| **Contratos relacionados** | Usa CT-02, CT-07 (`findById`), CT-05 caso B (`save`) y CT-10 (`evaluateProfile`) |

Este archivo documenta **dos interfaces separadas**: la HTTP (§1.A), que consume la `Web App`, y la de servicio (§1.B), que consume `SurveyRouter`.

## 1.A Interfaz HTTP — `SurveyRouter`

* **Componentes involucrados:** Solicita `Web App` y provee `SurveyRouter`.
* **Precondiciones (garantiza el solicitante):** Credencial según CT-02. `surveyId` va en la ruta y el cuerpo va vacío: el cliente **no** envía `userId` ni respuestas (se usan las persistidas).
* **Postcondiciones:** Obtiene `userId` por CT-02, delega en §1.B y responde `200` con `EvaluationResultResponse`, **también** cuando `evaluationStatus = ERROR`: por `BR-06`, el cliente recibe la categoría provisional y puede continuar. `totalScore` se serializa como `string` para no perder precisión (`docs/code_style.md` §7).

## 1.B Interfaz de servicio — `SurveyManager.completeSurvey(surveyId, userId)`

* **Componentes involucrados:** Solicita `SurveyRouter` y provee `SurveyManager` (en Python, `complete_survey(self, survey_id: UUID, user_id: UUID) -> EvaluationResult`).
* **Precondiciones (garantiza el solicitante):** `userId` no nulo obtenido de CT-02; `surveyId` con formato UUID.
* **Validaciones del proveedor (en este orden):**
  1. `SurveyRepository.findById(surveyId, userId)` (CT-07) devuelve una encuesta; si devuelve `null` → `NotFoundError`.
  2. `survey.status = DRAFT`; si no → `InvalidStateError`.
  3. Cada pregunta activa con `isRequired = true` tiene respuesta (`BR-03`); si no → `ValidationError`.
* **Postcondiciones (garantiza el proveedor):**
  1. Cierra la encuesta con `SurveyRepository.save` (CT-05, caso B), con `status = COMPLETED` y `completedAt = now()`. Si `save` devuelve `null` (otro cierre concurrente ganó) → `InvalidStateError`, sin evaluar.
  2. Ya confirmado el cierre, construye `List<ScoredAnswerDTO>` a partir de las respuestas **persistidas** y del `weight` de cada pregunta del catálogo.
  3. Invoca de forma síncrona `CategorizationService.evaluateProfile(userId, surveyId, scoredAnswers)` (CT-10) y devuelve su `EvaluationResult` sin modificarlo.
* **Invariantes:**
  * Una encuesta pasa a `COMPLETED` **exactamente una vez** y nunca vuelve a `DRAFT` (`BR-03`). Un fallo de evaluación no reabre la encuesta.
  * La evaluación ocurre solo después del commit del cierre.
  * Coherencia del resultado (`BR-06`): `evaluationStatus = ERROR` ⇔ `assignedCategory = UNDER_EVALUATION` ⇔ `totalScore = null`.
  * Privacidad: ninguna ruta registra respuestas, puntajes ni PII en logs.
* **Efectos secundarios:** La encuesta queda cerrada de forma permanente (`COMPLETED`, `completedAt`) y, por CT-10, se crea o actualiza el perfil financiero vigente del cliente.

## 2. Resultados de fallo

| Condición | Excepción de dominio | HTTP | Estado resultante |
|---|---|---|---|
| Credencial ausente, inválida o expirada | `UnauthorizedError` | 401 | Sin cambios |
| `surveyId` inexistente **o** de otro cliente | `NotFoundError` | 404 (nunca 403) | Sin cambios |
| Encuesta ya `COMPLETED`, incluido un cierre concurrente | `InvalidStateError` | 409 | Sin cambios; no se evalúa de nuevo |
| Faltan respuestas obligatorias (`BR-03`) | `ValidationError` | 422 | La encuesta sigue en `DRAFT` |
| Fallo del motor o de la persistencia definitiva, con perfil provisional guardado (`BR-06`) | — (no es una excepción: `EvaluationResult` con `ERROR`) | 200 con `evaluationStatus = ERROR` | Encuesta `COMPLETED`; perfil `UNDER_EVALUATION` |
| Fallo doble: también falla el guardado provisional | `EvaluationPersistenceError` (CT-10) | 503 *(propuesta; pendiente de decisión del stakeholder, `02` §5)* con mensaje genérico | Encuesta `COMPLETED`; perfil no garantizado |
| Fallo técnico al cerrar la encuesta | Excepción técnica; log sin PII | 500 genérico | La encuesta sigue en `DRAFT` (rollback) |

## 3. Estructura esencial (`.json`)

```json
{
  "http": {
    "path": { "surveyId": "UUID (requerido)" },
    "body": "vacío",
    "output": {
      "surveyId": "UUID (requerido)",
      "assignedCategory": "FinancialCategory (requerido; CONSERVATIVE | MODERATE | AGGRESSIVE | UNDER_EVALUATION)",
      "evaluationStatus": "EvaluationStatus (requerido; COMPLETED | ERROR)",
      "totalScore": "string | null (Decimal serializado, p. ej. \"57.50\"; null si y solo si evaluationStatus = ERROR)"
    }
  },
  "service": {
    "input": {
      "surveyId": "UUID (requerido)",
      "userId": "UUID (requerido; inyectado por CT-02)"
    },
    "output": "EvaluationResult (surveyId: UUID, assignedCategory: FinancialCategory, evaluationStatus: EvaluationStatus, totalScore: Decimal | null)"
  }
}
```

## 4. Especificación HTTP (OpenAPI)

```yaml
paths:
  /api/surveys/{surveyId}/complete:
    post:
      operationId: completeSurvey
      summary: Cierra la encuesta DRAFT (BR-03) y evalúa la categoría financiera inicial (BR-04..BR-06)
      security: [{ bearerAuth: [] }]
      parameters:
        - { name: surveyId, in: path, required: true, schema: { type: string, format: uuid } }
      responses:
        "200":
          description: Encuesta cerrada; categoría definitiva (COMPLETED) o provisional (ERROR, BR-06)
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EvaluationResultResponse" }
        "401": { description: No autenticado }
        "404": { description: Encuesta inexistente o ajena }
        "409": { description: Encuesta ya COMPLETED }
        "422": { description: Faltan respuestas obligatorias }
        "503": { description: "No fue posible completar la evaluación (fallo doble; código pendiente de decisión)" }
components:
  schemas:
    EvaluationResultResponse:
      type: object
      required: [surveyId, assignedCategory, evaluationStatus, totalScore]
      additionalProperties: false
      properties:
        surveyId: { type: string, format: uuid }
        assignedCategory: { type: string, enum: [CONSERVATIVE, MODERATE, AGGRESSIVE, UNDER_EVALUATION] }
        evaluationStatus: { type: string, enum: [COMPLETED, ERROR] }
        totalScore:
          type: string
          nullable: true
          pattern: "^\\d+(\\.\\d+)?$"
```

## 5. Notas de alineación y preguntas abiertas

* `01` §3.2 debería añadir el enum `EvaluationStatus { COMPLETED, ERROR }` y cambiar `EvaluationResult.status : String` por `evaluationStatus : EvaluationStatus`, con `totalScore : Decimal | null`.
* **Abierta (`02` §3.2):** si el cliente pierde la respuesta HTTP de un cierre exitoso, un reintento recibe 409. Hace falta una operación de consulta del perfil vigente (`CategorizationRouter` / `ProfileRepository.findByUserId`) para recuperar el resultado; no está cubierta por estos 12 contratos.
