# CT-03 — `SurveyManager.startSurvey`

| | |
|---|---|
| **Versión** | 1.2 (2026-11-12) — aprobado tras cierre de bloqueante `question_option` |
| **Estado** | Aprobado |
| **Trazabilidad** | `REQ-01` · US-01 · AC-01.1, AC-01.2 · `BR-01`, `BR-02` · `02` §1.1, §2.4 (fila `startSurvey`) · `01` §3.2 (`SurveyManager.startSurvey(userId : UUID) Survey`) |
| **Contratos relacionados** | Lo invoca CT-01; usa CT-04 (`findDraftByUserId`) y CT-05 (`save`) |

## 1. Descripción y características del contrato

* **Componentes involucrados:** Solicita `SurveyRouter` y provee `SurveyManager` (`startSurvey(userId)`; en Python, `start_survey(self, user_id: UUID) -> Survey`).
* **Precondiciones (garantiza el solicitante):** `userId` es un `UUID` no nulo obtenido de CT-02.
* **Validaciones del proveedor:** El catálogo activo contiene **entre 1 y 10** preguntas con `weight >= 0` (`BR-01`). Si no se cumple, es un error de configuración, no del cliente.
* **Postcondiciones (garantiza el proveedor):**
  1. Consulta `SurveyRepository.findDraftByUserId(userId)` (CT-04).
  2. Si devuelve `null`, crea una `Survey` con `status = DRAFT` y `startedAt = now()` y la persiste con `SurveyRepository.save` (CT-05). Si otra petición concurrente ya creó el borrador, `save` devuelve ese borrador ganador (CT-05, caso A).
  3. Si ya existía, lo reutiliza sin modificarlo.
  4. Retorna la `Survey` en `DRAFT` con `questions` (catálogo activo) y `answers` (respuestas ya registradas) cargadas.
* **Invariantes:** Tras la operación, el cliente tiene **exactamente un** borrador `DRAFT` (`BR-02`), aunque haya llamadas concurrentes. Nunca se modifica una encuesta `COMPLETED`.
* **Efectos secundarios:** A lo sumo un nuevo borrador `DRAFT` para `userId`; ninguno si ya existía.

## 2. Resultados de fallo

| Condición | Excepción / resultado | Traducción en `SurveyRouter` | Estado resultante |
|---|---|---|---|
| Catálogo activo vacío o con más de 10 preguntas | Error técnico (configuración inválida de `BR-01`); log técnico sin PII | 500 genérico | No se crea borrador |
| Fallo de persistencia en `save` | Error técnico propagado | 500 genérico | No se crea borrador (rollback) |

## 3. Estructura esencial (`.json`)

```json
{
  "input": {
    "userId": "UUID (requerido; proviene de CT-02)"
  },
  "output": {
    "survey": {
      "surveyId": "UUID",
      "userId": "UUID",
      "status": "SurveyStatus (DRAFT)",
      "startedAt": "datetime",
      "questions": "List<Question> (1..10; questionId: int, text: string, weight: Decimal >= 0, displayOrder: int, isRequired: boolean, options: List<AnswerOption>)",
      "answers": "List<Answer> (0..10; questionId: int, selectedOption: int, optionValue: Decimal)"
    }
  }
}
```

*Nota:* esta es la entidad de dominio interna. `SurveyRouter` la transforma al DTO `SurveyDraftResponse` de CT-01, que **omite** `weight` y `optionValue`.

## 4. Notas de alineación con `01` / `02`

> **Estado:** resuelto en `01` v1.2 y `02` v1.3 (2026-11-12). Se conserva como registro del cambio.

* `01` §3.2 debería añadir a `Survey` los atributos `answers : List~Answer~` y `startedAt : DateTime`, y a `Question` los atributos `displayOrder : Integer`, `isRequired : Boolean` y `options : List~AnswerOption~` (resuelto mediante `question_option` en `02` §2.2).
