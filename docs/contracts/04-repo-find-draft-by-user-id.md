# CT-04 — `SurveyRepository.findDraftByUserId`

| | |
|---|---|
| **Versión** | 1.1 (2026-11-12) — incorpora hallazgos F-01…F-21 de la auditoría de contratos |
| **Estado** | Propuesto |
| **Trazabilidad** | `REQ-01` · AC-01.2 · `BR-02` · `02` §1.1, §1.2 (mensaje `findDraftByUserId(userId)`), §2.5 · `01` §3.2 (`SurveyRepository`) |
| **Contratos relacionados** | Lo invoca CT-03 |

## 1. Descripción y características del contrato

* **Componentes involucrados:** Solicita `SurveyManager` y provee `SurveyRepository` (`findDraftByUserId(userId)`; en Python, `find_draft_by_user_id(self, user_id: UUID) -> Survey | None`).
* **Precondiciones (garantiza el solicitante):** `userId` es un `UUID` no nulo obtenido de CT-02 (equivale a `client.client_id`).
* **Postcondiciones (garantiza el proveedor):**
  * Ejecuta la consulta filtrando estrictamente por propietario y estado (`WHERE client_id = :userId AND status = 'DRAFT'`).
  * Si existe, devuelve la `Survey` con `answers` (todas las respuestas persistidas) y `questions` (catálogo activo, `is_active = true`, ordenado por `display_order`) cargadas.
  * Si el cliente no tiene borrador activo, devuelve `null`.
* **Invariantes:**
  * Por el índice único parcial `(client_id) WHERE status = 'DRAFT'` (`BR-02`), el resultado es a lo sumo una fila.
  * Nunca devuelve encuestas de otro `client_id` ni encuestas `COMPLETED`.
* **Efectos secundarios:** Ninguno (solo lectura sobre `survey`, `answer` y `question`).

## 2. Resultados de fallo

| Condición | Resultado | Estado resultante |
|---|---|---|
| El cliente no tiene borrador | `null` (no es un error) | Sin cambios |
| Fallo de conexión o consulta | Excepción técnica de persistencia propagada al servicio | Sin cambios |

## 3. Estructura esencial (`.json`)

```json
{
  "input": {
    "userId": "UUID (requerido; client_id del propietario)"
  },
  "output": {
    "draft": "Survey | null (surveyId, userId, status = DRAFT, startedAt, questions: List<Question>, answers: List<Answer>)"
  }
}
```

## 4. Notas de alineación con `01`

* `01` §3.2 declara `findDraftByUserId(userId : UUID) Survey`; debería declarar `Survey | null` (o `Optional~Survey~`) para reflejar que puede no haber borrador.
