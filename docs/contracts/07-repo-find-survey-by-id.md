# CT-07 — `SurveyRepository.findById`

| | |
|---|---|
| **Versión** | 1.2 (2026-11-12) — aprobado tras cierre de bloqueante `question_option` |
| **Estado** | Aprobado |
| **Trazabilidad** | `REQ-01` · Riesgo de acceso no autorizado · `BR-03` · `02` §1.1, §1.3 (mensaje `findById(surveyId, userIdA)`), §3.2 (fila `findById`) · `01` §3.2 (`SurveyRepository.findById`) |
| **Contratos relacionados** | Lo invocan CT-06 y CT-09 |

## 1. Descripción y características del contrato

* **Componentes involucrados:** Solicita `SurveyManager` y provee `SurveyRepository` (`findById(surveyId, userId)`; en Python, `find_by_id(self, survey_id: UUID, user_id: UUID) -> Survey | None`).
* **Precondiciones (garantiza el solicitante):** `surveyId` y `userId` son `UUID` no nulos. `userId` proviene de CT-02.
* **Postcondiciones (garantiza el proveedor):**
  * Filtra estrictamente en la consulta por `WHERE survey_id = :surveyId AND client_id = :userId`; el filtro de propiedad es la última línea de defensa (`02` §2.2).
  * Si hay coincidencia, devuelve la `Survey` en el estado en que esté (`DRAFT` o `COMPLETED`), con `questions` (catálogo activo, incluidas `weight` y opciones de `question_option`) y `answers` cargadas.
  * Si no existe **o** pertenece a otro cliente, devuelve `null`, sin distinguir entre los dos casos.
* **Invariantes:**
  * Nunca devuelve una encuesta de otro `client_id`, así que no permite inferir la existencia de recursos ajenos.
  * Es una **lectura sin bloqueo**: el `status` leído sirve para validar y responder rápido, pero **no** es la garantía final contra escrituras concurrentes. Esa garantía la dan CT-05 (caso B) y CT-08, que vuelven a comprobar `status = 'DRAFT'` dentro de su transacción.
* **Efectos secundarios:** Ninguno (solo lectura sobre `survey`, `answer` y `question`).

## 2. Resultados de fallo

| Condición | Resultado | Traducción en capas superiores | Estado resultante |
|---|---|---|---|
| No existe o pertenece a otro cliente | `null` (no es un error en el repositorio) | `SurveyManager` lanza `NotFoundError` → `SurveyRouter` responde 404 (nunca 403) | Sin cambios |
| Fallo de conexión o consulta | Excepción técnica de persistencia | 500 genérico | Sin cambios |

## 3. Estructura esencial (`.json`)

```json
{
  "input": {
    "surveyId": "UUID (requerido)",
    "userId": "UUID (requerido; client_id del propietario autenticado)"
  },
  "output": {
    "survey": "Survey | null (surveyId, userId, status: SurveyStatus, startedAt, completedAt | null, questions: List<Question>, answers: List<Answer>)"
  }
}
```

## 4. Notas de alineación con `01`

> **Estado:** resuelto en `01` v1.2 y `02` v1.3 (2026-11-12). Se conserva como registro del cambio.

* `01` §3.2 declara `findById(surveyId : UUID, userId : UUID) Survey`; debería declarar `Survey | null`, como ya describe `02` §3.2.
* La clase `Survey` del `01` debería añadir `answers : List~Answer~`, `startedAt : DateTime` y `completedAt : DateTime | null`.
