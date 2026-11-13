# CT-08 — `SurveyRepository.saveAnswer`

| | |
|---|---|
| **Versión** | 1.1 (2026-11-12) — incorpora hallazgos F-01…F-21 de la auditoría de contratos |
| **Estado** | Propuesto |
| **Trazabilidad** | `REQ-01` · AC-01.2 · `BR-03` · `02` §1.1 (mensaje `saveAnswer(surveyId, userId, answer)` hacia `SRepo`), §2.4 (fila `saveAnswer`), §2.5 · `01` §3.2 (`SurveyRepository.saveAnswer`) |
| **Contratos relacionados** | Lo invoca CT-06 |

## 1. Descripción y características del contrato

* **Componentes involucrados:** Solicita `SurveyManager` y provee `SurveyRepository` (`saveAnswer(surveyId, userId, answer)`; en Python, `save_answer(self, survey_id: UUID, user_id: UUID, answer: Answer) -> bool`).
* **Precondiciones (garantiza el solicitante):** `SurveyManager` ya comprobó, con la lectura de CT-07, la propiedad, el estado `DRAFT` y la validez de `questionId` y `selectedOption`, y resolvió `optionValue: Decimal` desde el catálogo del servidor.
* **Postcondiciones (garantiza el proveedor):** En **una única transacción**:
  1. Bloquea la fila de la encuesta **volviendo a comprobar propiedad y estado** bajo el bloqueo:
     ```sql
     SELECT survey_id FROM survey
      WHERE survey_id = :surveyId AND client_id = :userId AND status = 'DRAFT'
      FOR UPDATE;
     ```
  2. Si no hay fila, hace rollback sin escribir y devuelve `false`.
  3. Si hay fila, hace el *upsert* en `answer` sobre la restricción única `(survey_id, question_id)` con `selected_option` y `option_value` (`NUMERIC`), actualiza `survey.updated_at = now()`, confirma y devuelve `true`.
* **Invariantes:**
  * Ninguna respuesta se escribe sobre una encuesta `COMPLETED` (`BR-03`), ni siquiera si un `completeSurvey` se confirma entre la lectura de CT-07 y esta escritura: el bloqueo con `status = 'DRAFT'` serializa ambas operaciones (`02` §2.4).
  * A lo sumo una respuesta por (`survey_id`, `question_id`).
  * El repositorio no decide reglas de negocio: solo informa si la escritura se aplicó; `SurveyManager` traduce `false` a `InvalidStateError` (CT-06).
* **Efectos secundarios:** Si devuelve `true`: inserta o actualiza una fila en `answer` y actualiza `survey.updated_at`. Si devuelve `false`: ninguno.

## 2. Resultados de fallo

| Condición | Resultado | Estado resultante |
|---|---|---|
| La encuesta ya no está en `DRAFT` (cierre concurrente) | `false` → `InvalidStateError` (409) en CT-06 | Sin cambios |
| La encuesta no existe o es ajena (defensa en profundidad) | `false` | Sin cambios |
| Violación de clave foránea (`question_id` inexistente) | Excepción técnica de integridad; rollback | Sin cambios |
| Fallo de conexión o consulta | Excepción técnica de persistencia; rollback | Sin cambios |

## 3. Estructura esencial (`.json`)

```json
{
  "input": {
    "surveyId": "UUID (requerido)",
    "userId": "UUID (requerido; client_id del propietario)",
    "answer": {
      "questionId": "int (requerido)",
      "selectedOption": "int > 0 (requerido)",
      "optionValue": "Decimal (requerido; resuelto por el servidor, nunca por el cliente)"
    }
  },
  "output": {
    "applied": "boolean (true si se escribió; false si la encuesta no existe, es ajena o no está en DRAFT)"
  }
}
```

## 4. Notas de alineación con `01`

* `01` §3.2 declara `saveAnswer(surveyId : UUID, userId : UUID, answer : Answer) void`; debería declarar `Boolean` para que la comprobación de estado bajo bloqueo llegue al servicio.
