# CT-12 — `ProfileRepository.saveCategory`

| | |
|---|---|
| **Versión** | 1.1 (2026-11-12) — incorpora hallazgos F-01…F-21 de la auditoría de contratos |
| **Estado** | Propuesto |
| **Trazabilidad** | `REQ-01` · AC-01.1, AC-01.3 · `BR-04`, `BR-06` · `02` §1.1 (`saveCategory` con `COMPLETED` y con `UNDER_EVALUATION`/`ERROR`), §2.2 (`financial_profile`), §2.5 · `01` §3.2 (`ProfileRepository`) |
| **Contratos relacionados** | Lo invoca CT-10 (una vez en el caso exitoso; una o dos veces si hay fallo) |

## 1. Descripción y características del contrato

* **Componentes involucrados:** Solicita `CategorizationService` y provee `ProfileRepository` (`saveCategory(userId, evaluation)`; en Python, `save_category(self, user_id: UUID, evaluation: ProfileEvaluation) -> FinancialProfile`). Los datos de la evaluación se agrupan en el DTO `ProfileEvaluation` para respetar el máximo de 4 parámetros (`docs/code_style.md` §3.1).
* **Precondiciones (garantiza el solicitante):**
  * `userId` es el dueño autenticado.
  * `evaluation.surveyId` es una encuesta de ese cliente ya cerrada en `COMPLETED`. **Esta garantía es de `CategorizationService`/`SurveyManager`**: `ProfileRepository` no consulta la tabla `survey`, que pertenece al Módulo `survey` (`02` §2.3).
  * `evaluation` cumple la coherencia de `BR-06` (ver Invariantes).
* **Postcondiciones (garantiza el proveedor):** Ejecuta en una transacción un *upsert* sobre la clave única `financial_profile.client_id = :userId`, fijando `survey_id`, `assigned_category`, `evaluation_status`, `total_score` y `assigned_at = now()`. Retorna el `FinancialProfile` persistido.
* **Invariantes:**
  * A lo sumo un perfil por `client_id`; tras el éxito, exactamente uno, vinculado a `evaluation.surveyId` (`BR-04`).
  * Coherencia (`BR-06`): `evaluationStatus = ERROR` ⇔ `assignedCategory = UNDER_EVALUATION` ⇔ `totalScore = null`. `evaluationStatus = COMPLETED` ⇒ `assignedCategory` ∈ {`CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`} y `totalScore ≠ null`. Se recomienda reforzarla en datos con una restricción `CHECK` sobre `financial_profile`.
  * `total_score` se guarda como `NUMERIC` (`ADR-0001`).
* **Efectos secundarios:** Inserta o actualiza la única fila del cliente en `financial_profile`.

## 2. Resultados de fallo

| Condición | Resultado | Estado resultante |
|---|---|---|
| `evaluation` incoherente con `BR-06` (error de programación del llamador) | Excepción técnica (violación de `CHECK` o validación del DTO); rollback | Perfil sin cambios |
| Violación de clave foránea (`client_id` o `survey_id` inexistentes) | Excepción técnica de integridad; rollback | Perfil sin cambios |
| Fallo de conexión o consulta | Excepción técnica de persistencia; rollback. CT-10 la usa para pasar al flujo provisional (`BR-06`) o lanzar `EvaluationPersistenceError` | Perfil sin cambios |

## 3. Estructura esencial (`.json`)

```json
{
  "input": {
    "userId": "UUID (requerido; client_id del propietario del perfil)",
    "evaluation": {
      "surveyId": "UUID (requerido; encuesta origen ya COMPLETED)",
      "assignedCategory": "FinancialCategory (requerido; CONSERVATIVE | MODERATE | AGGRESSIVE | UNDER_EVALUATION)",
      "evaluationStatus": "EvaluationStatus (requerido; COMPLETED | ERROR)",
      "totalScore": "Decimal | null (null si y solo si evaluationStatus = ERROR)"
    }
  },
  "output": {
    "profile": "FinancialProfile (profileId, userId, surveyId, assignedCategory, evaluationStatus, totalScore | null, assignedAt)"
  }
}
```

## 4. Notas de alineación con `01` / `02`

* `01` §3.2 declara `saveCategory(userId, surveyId, category, status : String) void`. Debería pasar a `saveCategory(userId : UUID, evaluation : ProfileEvaluation) FinancialProfile`, porque la firma anterior no guardaba `total_score`, que sí existe en el modelo ER (`02` §2.2).
* Los diagramas de secuencia de `02` §1.1 deben actualizar sus mensajes a `saveCategory(userId, ProfileEvaluation(...))`.
