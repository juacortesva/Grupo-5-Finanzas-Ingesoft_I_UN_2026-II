# CT-06 — `saveAnswer` (HTTP + `SurveyManager`)

| | |
|---|---|
| **Versión** | 1.1 (2026-11-12) — incorpora hallazgos F-01…F-21 de la auditoría de contratos |
| **Estado** | Propuesto |
| **Trazabilidad** | `REQ-01` · US-01 · AC-01.1, AC-01.2 · `BR-01`, `BR-02`, `BR-03` · `02` §1.1 (loop `saveAnswer`), §1.3, §2.4, §3.2 (fila `saveAnswer`) · `01` §3.2 (`SurveyManager.saveAnswer`) |
| **Contratos relacionados** | Usa CT-02, CT-07 (`findById`) y CT-08 (`SurveyRepository.saveAnswer`) |

Este archivo documenta **dos interfaces separadas**: la HTTP (§1.A), que consume la `Web App`, y la de servicio (§1.B), que consume `SurveyRouter`.

## 1.A Interfaz HTTP — `SurveyRouter`

* **Componentes involucrados:** Solicita `Web App` y provee `SurveyRouter`.
* **Precondiciones (garantiza el solicitante):** Credencial según CT-02. `surveyId` va en la ruta y el cuerpo contiene solo `questionId` y `selectedOption`. El cliente **no** envía `userId` ni `optionValue`.
* **Postcondiciones:** Obtiene `userId` por CT-02, delega en §1.B y responde `204 No Content`. Traduce las excepciones de dominio a HTTP según §2.

## 1.B Interfaz de servicio — `SurveyManager.saveAnswer(surveyId, userId, answer)`

* **Componentes involucrados:** Solicita `SurveyRouter` y provee `SurveyManager` (en Python, `save_answer(self, survey_id: UUID, user_id: UUID, answer: Answer) -> None`).
* **Precondiciones (garantiza el solicitante):** `userId` no nulo obtenido de CT-02. `surveyId`, `questionId` y `selectedOption` con tipos válidos (Pydantic ya los validó).
* **Validaciones del proveedor (entrada no confiable, en este orden):**
  1. `SurveyRepository.findById(surveyId, userId)` (CT-07) devuelve una encuesta; si devuelve `null` → `NotFoundError`.
  2. `survey.status = DRAFT`; si no → `InvalidStateError`.
  3. `questionId` corresponde a una pregunta activa del catálogo de la encuesta; si no → `ValidationError`.
  4. `selectedOption` pertenece a las `options` de esa pregunta; si no → `ValidationError`.
* **Postcondiciones (garantiza el proveedor):** Resuelve `optionValue: Decimal` **desde el catálogo del servidor** (nunca desde el cliente) y delega en `SurveyRepository.saveAnswer` (CT-08). Al terminar con éxito, la respuesta de (`surveyId`, `questionId`) queda insertada o actualizada y `survey.updated_at` refleja la escritura. Si CT-08 indica que la escritura no se aplicó (la encuesta dejó de estar en `DRAFT` por un cierre concurrente) → `InvalidStateError`.
* **Invariantes:**
  * Una encuesta `COMPLETED` nunca acepta respuestas (`BR-03`). La comprobación definitiva ocurre bajo bloqueo en CT-08, no solo en la lectura de CT-07.
  * Ante cualquier fallo no se alteran datos existentes.
  * La operación es idempotente: repetir la misma respuesta deja el mismo estado.
* **Efectos secundarios:** Una respuesta registrada o actualizada en el borrador del cliente, en una transacción independiente (persistencia progresiva, `02` §1.1).

## 2. Resultados de fallo

| Condición | Excepción de dominio | HTTP | Estado resultante |
|---|---|---|---|
| Credencial ausente, inválida o expirada | `UnauthorizedError` | 401 | Sin cambios |
| `surveyId` inexistente **o** de otro cliente (indistinguibles) | `NotFoundError` | 404 (nunca 403, `02` §1.3) | Sin cambios |
| Encuesta `COMPLETED`, incluido un cierre concurrente detectado en CT-08 (`BR-03`) | `InvalidStateError` | 409 | Sin cambios |
| `questionId` inexistente o inactiva | `ValidationError` | 422 | Sin cambios |
| `selectedOption` no pertenece a la pregunta | `ValidationError` | 422 | Sin cambios |
| Cuerpo mal formado (tipos, campos extra o faltantes) | Validación Pydantic | 422 | Sin cambios |
| Fallo técnico de persistencia | Excepción técnica; log sin respuestas ni PII | 500 genérico | Sin cambios (rollback) |

## 3. Estructura esencial (`.json`)

```json
{
  "http": {
    "path": { "surveyId": "UUID (requerido)" },
    "body": {
      "questionId": "int >= 1 (requerido)",
      "selectedOption": "int >= 1 (requerido)"
    },
    "output": "vacío (204 No Content)"
  },
  "service": {
    "input": {
      "surveyId": "UUID (requerido)",
      "userId": "UUID (requerido; inyectado por CT-02, nunca del cliente)",
      "answer": {
        "questionId": "int (requerido)",
        "selectedOption": "int > 0 (requerido)"
      }
    },
    "output": "void"
  }
}
```

## 4. Especificación HTTP (OpenAPI)

```yaml
paths:
  /api/surveys/{surveyId}/answers:
    put:
      operationId: saveAnswer
      summary: Registra o actualiza una respuesta en el borrador DRAFT del cliente (persistencia progresiva)
      security: [{ bearerAuth: [] }]
      parameters:
        - { name: surveyId, in: path, required: true, schema: { type: string, format: uuid } }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [questionId, selectedOption]
              additionalProperties: false
              properties:
                questionId: { type: integer, minimum: 1 }
                selectedOption: { type: integer, minimum: 1 }
      responses:
        "204": { description: Respuesta registrada o actualizada }
        "401": { description: No autenticado }
        "404": { description: Encuesta inexistente o ajena }
        "409": { description: Encuesta COMPLETED (BR-03) }
        "422": { description: Pregunta u opción inválida, o cuerpo mal formado }
```

## 5. Notas de alineación

* **Dependencia abierta (`02` §5):** la validación de `selectedOption` y la resolución de `optionValue` dependen del catálogo de opciones por pregunta, que aún no tiene representación física. Es bloqueante para implementar.
