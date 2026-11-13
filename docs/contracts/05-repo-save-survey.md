# CT-05 — `SurveyRepository.save`

| | |
|---|---|
| **Versión** | 1.2 (2026-11-12) — aprobado |
| **Estado** | Aprobado |
| **Trazabilidad** | `REQ-01` · AC-01.1 · `BR-02`, `BR-03` · `02` §1.1 (mensajes `save(new Survey en DRAFT)` y `save(survey COMPLETED)`), §2.4, §2.5 · `01` §3.2 (`SurveyRepository.save`) |
| **Contratos relacionados** | Lo invocan CT-03 (caso A) y CT-09 (caso B) |

## 1. Descripción y características del contrato

* **Componentes involucrados:** Solicita `SurveyManager` y provee `SurveyRepository` (`save(survey)`; en Python, `save(self, survey: Survey) -> Survey | None`).
* **Precondiciones (garantiza el solicitante):** `survey.userId` es el `userId` obtenido de CT-02. Solo se admiten dos casos:
  * **Caso A — crear borrador:** `survey` es nueva (sin fila previa), con `status = DRAFT` y `startedAt` fijado.
  * **Caso B — cerrar encuesta:** `survey` existe, `SurveyManager` ya verificó la completitud de las respuestas obligatorias (`BR-03`) y la entrega con `status = COMPLETED` y `completedAt` fijado.
  
  Cualquier otra transición (por ejemplo `COMPLETED → DRAFT`) está fuera de contrato y no se persiste.
* **Postcondiciones (garantiza el proveedor):**
  * **Caso A:** inserta la fila en una transacción y devuelve la `Survey` persistida (con `surveyId`, `questions` y `answers` vacía). Si el índice único parcial `(client_id) WHERE status = 'DRAFT'` rechaza la inserción por una carrera concurrente, **no propaga el error**: relee y devuelve el `DRAFT` ganador (`02` §2.4).
  * **Caso B:** ejecuta una transición **condicional y atómica**:
    ```sql
    UPDATE survey
       SET status = 'COMPLETED', completed_at = :completedAt, updated_at = now()
     WHERE survey_id = :surveyId AND client_id = :userId AND status = 'DRAFT'
    RETURNING *;
    ```
    Si afecta 1 fila, confirma (`commit`) y devuelve la `Survey` cerrada. Si afecta 0 filas (no existe, es ajena o ya no está en `DRAFT`), no modifica nada y devuelve `null`. El repositorio no decide la causa: la interpreta `SurveyManager` (CT-09).
* **Invariantes:**
  * A lo sumo un `DRAFT` por `client_id` (`BR-02`).
  * `completed_at` se escribe **una sola vez**: la condición `status = 'DRAFT'` impide que dos cierres concurrentes la sobrescriban o disparen dos evaluaciones (`BR-03`).
  * Toda escritura se filtra por `client_id = :userId`.
* **Efectos secundarios:** Caso A: inserta una fila en `survey`. Caso B: actualiza `status`, `completed_at` y `updated_at` de una fila de `survey`. Nunca toca `answer`.

## 2. Resultados de fallo

| Condición | Resultado | Estado resultante |
|---|---|---|
| Caso A: conflicto con el índice único parcial | Devuelve el `DRAFT` existente (no es un error) | Un único `DRAFT` |
| Caso B: 0 filas afectadas | `null` → `SurveyManager` lo traduce a `InvalidStateError` (409) | Sin cambios |
| Fallo de conexión o consulta | Excepción técnica de persistencia; rollback | Sin cambios |

## 3. Estructura esencial (`.json`)

```json
{
  "input": {
    "survey": {
      "surveyId": "UUID (requerido)",
      "userId": "UUID (requerido)",
      "status": "SurveyStatus (DRAFT en caso A | COMPLETED en caso B)",
      "startedAt": "datetime (requerido en caso A)",
      "completedAt": "datetime | null (requerido y no nulo en caso B; null en caso A)"
    }
  },
  "output": {
    "survey": "Survey | null (entidad persistida; null solo en caso B con 0 filas afectadas)"
  }
}
```

## 4. Notas de alineación con `01` / `02`

> **Estado:** resuelto en `01` v1.2 y `02` v1.3 (2026-11-12). Se conserva como registro del cambio.

* `01` §3.2 declara `save(survey : Survey) void`; debería declarar `Survey | null` para devolver el `surveyId` generado (que `02` §1.1 ya muestra como `persisted DRAFT`) y el resultado de la transición condicional.
* Si el equipo prefiere mayor cohesión, este contrato puede dividirse en `createDraft` y `completeTransition` sin cambiar la semántica descrita.
