# CT-01 — `startSurvey` (HTTP)

| | |
|---|---|
| **Versión** | 1.2 (2026-11-12) — cierra bloqueante `question_option` y formato de errores HTTP |
| **Estado** | Aprobado |
| **Trazabilidad** | `REQ-01` · US-01 · AC-01.1, AC-01.2 · `BR-01`, `BR-02` · `02` §1.1 (mensaje `startSurvey() [HTTP]`), §1.2 · `01` §2.2 (`SurveyRouter`) |
| **Contratos relacionados** | CT-02 (`getCurrentUser`), CT-03 (`SurveyManager.startSurvey`) |

## 1. Descripción y características del contrato

* **Componentes involucrados:** Solicita `Web App` (Capa de Presentación) y provee `SurveyRouter` (Capa HTTP del Módulo `survey`).
* **Precondiciones (garantiza el solicitante):** La petición incluye la credencial de sesión según CT-02. El cuerpo va vacío: la identidad **nunca** viaja en el cuerpo ni en la ruta.
* **Postcondiciones (garantiza el proveedor):** `SurveyRouter` obtiene `userId` mediante CT-02, delega en `SurveyManager.startSurvey(userId)` (CT-03) y responde con el **único** borrador `DRAFT` del cliente (`BR-02`), ya sea recién creado o existente, junto con:
  * el catálogo de preguntas activas (entre 1 y 10, `BR-01`), ordenado por `displayOrder`;
  * las respuestas ya registradas en ese borrador (lista vacía si es nuevo), para que la `Web App` derive `nextQuestion` = primera pregunta con `isRequired = true` sin respuesta (`02` §1.2, AC-01.2).
* **Invariantes:**
  * Idempotencia: N invocaciones del mismo cliente devuelven el mismo `surveyId` mientras el borrador siga en `DRAFT`.
  * Ocultamiento de información: la respuesta **no** expone `weight` ni `optionValue`; esos valores solo los usa el backend.
* **Efectos secundarios:** Si el cliente no tenía borrador, queda registrado exactamente un nuevo borrador `DRAFT`; en caso contrario, ninguno.

## 2. Resultados de fallo

| Condición | Excepción de dominio | HTTP | Estado resultante |
|---|---|---|---|
| Credencial ausente, inválida o expirada | `UnauthorizedError` (CT-02) | 401 | Sin cambios |
| Catálogo activo vacío o con más de 10 preguntas (violación de configuración de `BR-01`) | Error técnico propagado desde CT-03 | 500 genérico, sin detalles internos; log técnico sin PII | Sin cambios |

## 3. Estructura esencial (`.json`)

```json
{
  "input": {},
  "output": {
    "surveyId": "UUID (requerido)",
    "status": "SurveyStatus (requerido; siempre DRAFT)",
    "startedAt": "datetime ISO-8601 (requerido)",
    "questions": [
      {
        "questionId": "int (requerido)",
        "text": "string (requerido)",
        "displayOrder": "int (requerido; único en el catálogo activo)",
        "isRequired": "boolean (requerido)",
        "options": [
          {
            "selectedOption": "int > 0 (requerido; question_option.option_number)",
            "label": "string (requerido; question_option.text)"
          }
        ]
      }
    ],
    "answers": [
      { "questionId": "int (requerido)", "selectedOption": "int > 0 (requerido)" }
    ]
  }
}
```

*Restricciones:* `questions` tiene entre 1 y 10 elementos. `answers` tiene entre 0 y `questions.length` elementos, con `questionId` únicos.

## 4. Especificación HTTP (OpenAPI)

```yaml
paths:
  /api/surveys:
    post:
      operationId: startSurvey
      summary: Inicia o recupera el único borrador DRAFT del cliente autenticado (BR-02)
      security: [{ bearerAuth: [] }]
      responses:
        "200":
          description: Borrador DRAFT (nuevo o existente; operación idempotente)
          content:
            application/json:
              schema: { $ref: "#/components/schemas/SurveyDraftResponse" }
        "401":
          description: No autenticado
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ErrorResponse" }
        "500":
          description: Error interno genérico (sin detalles)
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ErrorResponse" }
components:
  schemas:
    ErrorResponse:
      type: object
      required: [detail]
      properties:
        detail: { type: string }
    SurveyDraftResponse:
      type: object
      required: [surveyId, status, startedAt, questions, answers]
      additionalProperties: false
      properties:
        surveyId: { type: string, format: uuid }
        status: { type: string, enum: [DRAFT] }
        startedAt: { type: string, format: date-time }
        questions:
          type: array
          minItems: 1
          maxItems: 10
          items: { $ref: "#/components/schemas/QuestionDTO" }
        answers:
          type: array
          maxItems: 10
          items: { $ref: "#/components/schemas/AnswerDTO" }
    QuestionDTO:
      type: object
      required: [questionId, text, displayOrder, isRequired, options]
      additionalProperties: false
      properties:
        questionId: { type: integer, minimum: 1 }
        text: { type: string, minLength: 1 }
        displayOrder: { type: integer, minimum: 1 }
        isRequired: { type: boolean }
        options:
          type: array
          minItems: 1
          items:
            type: object
            required: [selectedOption, label]
            additionalProperties: false
            properties:
              selectedOption: { type: integer, minimum: 1 }
              label: { type: string, minLength: 1 }
    AnswerDTO:
      type: object
      required: [questionId, selectedOption]
      additionalProperties: false
      properties:
        questionId: { type: integer, minimum: 1 }
        selectedOption: { type: integer, minimum: 1 }
```

## 5. Notas de alineación

* **Resuelto (Fase 0 — 2026-11-12):** `options` se respalda físicamente en la tabla `question_option (id, question_id, option_number, text, value)` definida en `02` §2.2, exponiendo `{ selectedOption, label }` (`option_number` y `text`) y ocultando `value`.
* La ruta `/api/surveys` es una ruta aprobada, coherente con `docs/code_style.md` (`/api/surveys/{id}/complete`).
