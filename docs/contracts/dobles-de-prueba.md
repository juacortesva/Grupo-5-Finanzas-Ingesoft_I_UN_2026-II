# Dobles de prueba de la capa de servicio

| | |
|---|---|
| **Versión** | 1.0 (2026-11-26) — SCRUM-11 (inicio y evaluación) |
| **Estado** | En revisión |
| **Trazabilidad** | `REQ-01` · CT-03, CT-09, CT-10, CT-11 · `ADR-0003` (frontera por DTOs) · `docs/code_style.md` §8 (AAA y nomenclatura de pruebas) |
| **Código** | `backend/tests/doubles/` |

## 1. Propósito

Los dobles permiten que cada capa se desarrolle y se pruebe **en paralelo y sin base de datos**, cumpliendo los contratos de `docs/contracts/`:

* Quien implementa la **API** (`SurveyRouter`) prueba su traducción HTTP con un `SurveyManager` simulado, sin esperar al servicio real.
* Quien implementa el **servicio** (`SurveyManager`, `CategorizationService`) lo prueba con repositorios en memoria, sin esperar a la persistencia real.
* Quien implementa la **persistencia** (`SqlAlchemySurveyRepository`, `SqlAlchemyProfileRepository`) tiene en los fakes una especificación ejecutable del comportamiento que el servicio espera de CT-04, CT-05, CT-07, CT-08 y CT-12.

Tipos usados (terminología de Meszaros):

* **Stub:** responde con datos fijos o lanza un error configurado; registra las llamadas recibidas.
* **Fake:** implementación funcional simplificada (en memoria) que respeta las reglas de negocio del contrato.

## 2. Catálogo de dobles

| Doble | Tipo | Reemplaza a | Contratos que simula | Lo usa |
|---|---|---|---|---|
| `StubSurveyManager` | Stub | `SurveyManager` | CT-03 (`start_survey`), CT-09 (`complete_survey`) | Capa API (`SurveyRouter`) |
| `InMemorySurveyRepository` | Fake | `SqlAlchemySurveyRepository` | CT-04, CT-05, CT-07, CT-08 | Capa de servicio (`SurveyManager`) |
| `StubCategorizationService` | Stub | `CategorizationService` | CT-10 | Capa de servicio (`SurveyManager`) |
| `InMemoryProfileRepository` | Fake | `SqlAlchemyProfileRepository` | CT-12 | Capa de servicio (`CategorizationService`) |

Funciones de apoyo (`survey_doubles.py`): `build_question`, `build_catalog`, `build_survey` y `build_result` construyen entidades de dominio válidas para la sección *Arrange* de las pruebas.

## 3. Comportamiento garantizado por cada doble

### 3.1 `StubSurveyManager`

* `start_survey(user_id)` → devuelve el borrador configurado (`draft`, por defecto 2 preguntas obligatorias en `DRAFT` y sin respuestas) con `user_id` del llamador.
* `complete_survey(survey_id, user_id)` → devuelve un `EvaluationResult` coherente con `BR-06` según `result_category`: `MODERATE` / `COMPLETED` / `65.00` por defecto, o `UNDER_EVALUATION` / `ERROR` / `null`.
* Si se asigna `error` (por ejemplo `NotFoundError`, `InvalidStateError`, `ValidationError` o `EvaluationPersistenceError`), toda operación lo lanza, para verificar la traducción a 404, 409, 422 o 503.
* `calls` registra el nombre de cada operación invocada.

### 3.2 `InMemorySurveyRepository`

* `find_by_id` devuelve `None` tanto si la encuesta no existe como si es de otro cliente (`ADR-0006`).
* `save` de un `DRAFT` devuelve el borrador existente si el cliente ya tiene uno (CT-05 caso A, `BR-02`); `save` de un `COMPLETED` solo aplica si la encuesta sigue en `DRAFT` (CT-05 caso B, `BR-03`) y en otro caso devuelve `None`.
* `save_answer` inserta o reemplaza la respuesta de la pregunta y devuelve `False` si la encuesta no está en `DRAFT` (CT-08).
* Interruptores: `fail_on_save` (lanza un error técnico en `save`) y `simulate_concurrent_close` (simula que otra petición cerró la encuesta).
* `save_calls` cuenta las invocaciones de `save`.

### 3.3 `StubCategorizationService`

* `evaluate_profile` devuelve `build_result(survey_id, result_category)` y registra `(user_id, survey_id, answers)` en `calls`, para verificar que `SurveyManager` envía los `ScoredAnswerDTO` con `Decimal`.

### 3.4 `InMemoryProfileRepository`

* `save_category` hace *upsert* por `user_id` (un perfil vigente, `BR-04`) y registra cada `ProfileEvaluation` recibida en `received`.

## 4. Uso

### 4.1 Probar la API con `StubSurveyManager`

```python
from src.core.auth_deps import get_current_user
from src.core.exceptions import NotFoundError
from src.main import app
from src.survey.service import get_survey_manager
from tests.doubles.survey_doubles import StubSurveyManager

stub = StubSurveyManager(error=NotFoundError("Encuesta no encontrada"))
app.dependency_overrides[get_survey_manager] = lambda: stub
app.dependency_overrides[get_current_user] = lambda: USER_ID
# POST /api/surveys/{id}/complete → 404 {"detail": "Encuesta no encontrada"}
```

Ejemplo completo: `backend/tests/survey/test_survey_router_with_stub.py`.

### 4.2 Probar el servicio con fakes

```python
repo = InMemorySurveyRepository(build_catalog())
stub = StubCategorizationService()
manager = SurveyManager(repo, stub)
draft = repo.add(build_survey(USER_ID, repo.questions))
```

Ejemplos completos: `backend/tests/survey/test_survey_manager_unit.py` y `backend/tests/categorization/test_categorization_service_unit.py`.

## 5. Reglas

* Los dobles viven solo en `backend/tests/` y **nunca** se importan desde `src/`.
* Un doble no puede contradecir su contrato: si un contrato cambia de versión, el doble se actualiza en el mismo PR.
* Las pruebas siguen `test_<operacion>_when_<condicion>_then_<resultado>` y la estructura AAA (`docs/code_style.md` §8).
