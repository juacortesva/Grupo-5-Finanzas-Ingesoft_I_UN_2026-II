# Estado del Proyecto y Memoria de Contexto — Asesor Financiero Personal

| | |
| :--- | :--- |
| **Equipo** | Grupo 5 (`@KevinVerjan`, `@Estebandido-exe`, `@josuarezvi`, `@juacortesva`) |
| **Ubicación** | `docs/project_status.md` |
| **Asignatura** | Ingeniería de Software I — Universidad Nacional de Colombia (UNAL) 2026-II |
| **Última Actualización** | 2026-11-12 |
| **Estado Global** | Contratos de interfaz `CT-01`..`CT-12` (v1.2) **Aprobados** y alineados con `01` v1.2 y `02` v1.3 / Bloqueantes de Fase 0 resueltos (`question_option`, auth provisional `CT-02`, formato de errores HTTP) / En ejecución: **Fase 0 — Walking Skeleton** (`ADR-0002`) |
| **Referencias** | `docs/code_style.md`, `docs/estructura_repositorio.md`, `docs/adr/adr-0001.md`, `docs/adr/adr-0002.md`, `docs/req/REQ-01.md`, `docs/design/01_Architectural_and_Detailed_Design.md`, `docs/design/02_Interaction_and_Data_Design.md`, `docs/contracts/` |

---

## 1. Propósito de este Documento (Instrucciones para la IA)

Este archivo actúa como la **Fuente Única de Verdad (Single Source of Truth)** sobre el estado actual del repositorio, las decisiones de arquitectura aprobadas, las reglas de negocio y el plan de trabajo incremental del proyecto **Asesor Financiero Personal**.

Cualquier asistente de IA que reciba este documento debe:
1. **Respetar estrictamente la arquitectura, capas y convenciones** aquí descritas sin inventar módulos, colas de mensajes (brokers) ni tecnologías fuera del stack aprobado en `ADR-0001`.
2. **Distinguir entre lo que ya existe en el repositorio (Sección 3.1) y lo que está pendiente de construir (Sección 3.2 y Sección 6)**.
3. **Aplicar todas las restricciones de código de `docs/code_style.md`** (tipado estricto, aritmética `Decimal`, privacidad en logs y límites de complejidad).

---

## 2. Resumen del Sistema y Reglas Inmutables

### 2.1 Propósito del Sistema (`REQ-01`)
Aplicación web interactiva que permite a los usuarios descubrir y registrar su perfil financiero mediante una encuesta breve de *onboarding* (máximo 10 preguntas, menos de 3 minutos), evaluando sus respuestas contra una matriz de ponderación para asignar una categoría de inicio (`CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`) que personalice su plan financiero.

### 2.2 Matriz de Decisiones Arquitectónicas y Reglas de Negocio

| Identificador | Regla / Decisión | Restricción Técnica Obligatoria |
| :--- | :--- | :--- |
| **`ADR-0001`** | **Stack Tecnológico Políglota** | **Frontend:** React + Vite + TypeScript 5+. **Backend:** Python 3.11+ con FastAPI, SQLAlchemy 2.0 y Pydantic v2. **Base de Datos:** PostgreSQL. |
| **`ADR-0001` / `code_style.md`** | **Precisión Numérica Estricta (Cero `float`)** | **Prohibido usar `float`** para puntajes, pesos de preguntas, valores de opción o montos. En Python se usa exclusivamente `decimal.Decimal` inicializado desde `str` o `int` (ej. `Decimal("0.15")`). En PostgreSQL se usa `NUMERIC(precision, scale)` con `asdecimal=True`. En TypeScript viajan como `string`. |
| **`ADR-0002`** | **Construcción Híbrida Incremental** | **Fase 0:** *Walking Skeleton* (tubería E2E mínima). **Fases 1 a 3:** *Vertical Slices* por escenario de `REQ-01`. Prohibido desarrollar por capas horizontales aisladas. |
| **`estructura_repositorio.md`** | **Arquitectura Modular y Data Ownership** | División primaria por módulos de dominio (`survey/`, `categorization/`) y secundaria por capas (`router` $\rightarrow$ `service` $\rightarrow$ `engine`/`repository` $\rightarrow$ `models`). Ningún módulo puede importar `models.py` o `repository.py` de otro módulo. |
| **`BR-01`** | **Acotación del Cuestionario** | La encuesta activa consta de un **máximo de 10 preguntas parametrizadas** en la tabla `question` con peso no negativo. |
| **`BR-02`** | **Unicidad de Borrador (`DRAFT`)** | Un cliente puede tener **a lo sumo un borrador (`DRAFT`) activo** a la vez; al reingresar retoma ese mismo borrador sin perder respuestas previas. |
| **`BR-03`** | **Completitud e Inmutabilidad (`COMPLETED`)** | La encuesta solo pasa a `COMPLETED` con todas las preguntas obligatorias respondidas. Una vez `COMPLETED`, es **inmutable** y rechaza modificaciones (`InvalidStateError`). |
| **`BR-04`** | **Categoría Única Vigente** | Todo cliente que completa la encuesta obtiene exactamente una categoría inicial vigente en `financial_profile` vinculada a la encuesta origen. |
| **`BR-05`** | **Desempate Conservador en Umbral** | Si el puntaje calculado se ubica exactamente en el límite (`<=`) entre dos categorías financieras, `ScoringEngine.determine_category` asigna por defecto la categoría de **menor riesgo** (más conservadora). |
| **`BR-06`** | **Asignación Provisional ante Fallo** | Si falla el cálculo o persistencia al evaluar, **no se lanza HTTP 500** ni se usan colas asíncronas. Se captura el error, se asigna `UNDER_EVALUATION` con `evaluation_status = 'ERROR'` y `total_score = null`, sin reabrir la encuesta `COMPLETED` (y propagando `EvaluationPersistenceError` ante fallo doble). |
| **Seguridad y Privacidad** | **Protección de Datos y Logs (`REQ-01`)** | El `user_id` (`client_id` en BD) se extrae siempre de la dependencia de autenticación del backend, nunca del body HTTP. **Prohibido registrar en logs (`logger.error`, `print`) las respuestas (`answers`), puntajes (`total_score`) o datos personales del usuario.** |

---

## 3. Estructura de Directorios (Realidad Actual vs. Arquitectura Objetivo)

### 3.1 Estado Actual en el Repositorio
Actualmente el repositorio contiene **exclusivamente la documentación de ingeniería aprobada**. Aún no se han creado las carpetas `backend/`, `frontend/` ni el archivo `docker-compose.yml`:

```text
Grupo-5-Finanzas-Ingesoft_I_UN_2026-II/
├── README.md
└── docs/
    ├── code_style.md                                    # Estándares Ruff, ESLint, Decimal, Logs
    ├── estructura_repositorio.md                        # Reglas de monorepo y capas
    ├── project_status.md                                # Estado actualizado del proyecto (este archivo)
    ├── adr/
    │   ├── adr-0001.md                                  # Selección del Stack (React, FastAPI, PostgreSQL)
    │   └── adr-0002.md                                  # Estrategia Walking Skeleton + Vertical Slices
    ├── contracts/                                       # Contratos de interfaz CT-01..CT-12 (DbC + OpenAPI), ver §5.3
    │   ├── 01-http-start-survey.md
    │   ├── 02-auth-get-current-user.md
    │   ├── 03-service-start-survey.md
    │   ├── 04-repo-find-draft-by-user-id.md
    │   ├── 05-repo-save-survey.md
    │   ├── 06-http-and-service-save-answer.md
    │   ├── 07-repo-find-survey-by-id.md
    │   ├── 08-repo-save-answer.md
    │   ├── 09-http-and-service-complete-survey.md
    │   ├── 10-service-evaluate-profile.md
    │   ├── 11-engine-scoring.md
    │   └── 12-repo-save-category.md
    ├── design/
    │   ├── 01_Architectural_and_Detailed_Design.md      # Componentes, diagramas de clases y responsabilidades
    │   └── 02_Interaction_and_Data_Design.md            # Diagramas de secuencia, modelo ER y contratos
    ├── req/
    │   └── REQ-01.md                                    # Requerimiento Capstone validado (US-01, AC-01.1 a 01.3)
    └── rfc/
        └── rfc_proyecto.md                              # Propuesta conceptual inicial
```

### 3.2 Árbol Objetivo Completo del Monorepo (Integrando `docs/` Existente + Código por Construir)
Esta es la estructura completa hacia la cual evolucionará el repositorio durante las Fases 0 a 3, conservando intacta la carpeta `docs/`:

```text
Grupo-5-Finanzas-Ingesoft_I_UN_2026-II/
├── README.md                                            # Descripción general e instrucciones de arranque
├── docker-compose.yml                                   # Para levantar backend y frontend en la VM (BD en servidor del profesor)
├── docs/                                                # Documentación de Ingeniería (YA EXISTENTE)
│   ├── code_style.md                                    # Estándares Ruff, ESLint, Decimal, Logs
│   ├── estructura_repositorio.md                        # Reglas de monorepo y capas
│   ├── project_status.md                                # Estado actualizado del proyecto
│   ├── adr/
│   │   ├── adr-0001.md
│   │   └── adr-0002.md
│   ├── contracts/                                       # CT-01..CT-12
│   ├── design/
│   │   ├── 01_Architectural_and_Detailed_Design.md
│   │   └── 02_Interaction_and_Data_Design.md
│   ├── req/
│   │   └── REQ-01.md
│   └── rfc/
│       └── rfc_proyecto.md
├── backend/                                             # API REST y Lógica de Negocio (POR CONSTRUIR)
│   ├── pyproject.toml                                   # Configuración de dependencias, Ruff, Mypy y Pytest
│   ├── alembic/                                         # Migraciones de esquema de PostgreSQL
│   │   └── versions/
│   ├── src/
│   │   ├── main.py                                      # Punto de entrada de FastAPI y registro de routers
│   │   ├── core/                                        # database.py (SQLAlchemy), config.py, auth_deps.py (user_id), schemas.py
│   │   ├── survey/                                      # Módulo Survey (REQ-01)
│   │   │   ├── router.py                                # SurveyRouter (endpoints HTTP)
│   │   │   ├── service.py                               # SurveyManager (ciclo DRAFT/COMPLETED)
│   │   │   ├── repository.py                            # SurveyRepository (contrato + implementación SQLAlchemy)
│   │   │   ├── models.py                                # Tablas client, survey, question, question_option, answer
│   │   │   ├── schemas.py                               # DTOs Pydantic de entrada/salida (CamelCaseSchema)
│   │   │   └── enums.py                                 # SurveyStatus (DRAFT, COMPLETED)
│   │   └── categorization/                              # Módulo Categorization (REQ-01)
│   │       ├── router.py                                # CategorizationRouter
│   │       ├── service.py                               # CategorizationService (orquestación y fallback Escenario 3)
│   │       ├── engine.py                                # ScoringEngine (matriz Decimal y BR-05 aislados)
│   │       ├── repository.py                            # ProfileRepository (contrato + implementación SQLAlchemy)
│   │       ├── models.py                                # Tabla financial_profile
│   │       ├── schemas.py                               # EvaluationResult, ScoredAnswerDTO, ProfileEvaluation
│   │       └── enums.py                                 # FinancialCategory (CONSERVATIVE, MODERATE, AGGRESSIVE, UNDER_EVALUATION), EvaluationStatus (COMPLETED, ERROR)
│   └── tests/
│       ├── unit/                                        # Ej: test_scoring_engine.py (probar BR-05 sin BD)
│       └── integration/                                 # Ej: test_evaluate_profile.py (Escenarios 1, 2 y 3)
└── frontend/                                            # Aplicación Web Cliente React + Vite + TS (POR CONSTRUIR)
    ├── package.json                                     # Dependencias y scripts (openapi-typescript, vitest)
    ├── tsconfig.json                                    # Configuración estricta de TypeScript
    └── src/
        ├── api/                                         # Cliente HTTP y tipos autogenerados (openapi-typescript)
        │   └── generated/
        ├── features/
        │   ├── survey/                                  # Componentes y hooks del cuestionario (DRAFT/COMPLETED)
        │   │   ├── components/
        │   │   ├── hooks/
        │   │   ├── pages/
        │   │   └── types.ts
        │   └── categorization/                          # Pantalla de confirmación y resumen del plan
        │       ├── components/
        │       ├── hooks/
        │       ├── pages/
        │       └── types.ts
        └── shared/                                      # Componentes UI reutilizables (botones, alertas, spinners)
            ├── components/
            └── utils/
```

---

## 4. Estándares de Código, Naming y Reglas de Capas (`docs/code_style.md`)

### 4.1 Convenciones de Nombres (Naming Case)
- **Idioma:** Todo el código fuente (clases, métodos, variables, tablas, columnas) se escribe en **inglés**. Textos de UI, mensajes de error al usuario, docstrings y comentarios explicativos van en **español**.
- **Python (Backend):** `snake_case` para funciones, métodos, variables y módulos (`evaluate_profile`, `user_id`, `engine.py`). `PascalCase` para clases, modelos y schemas (`SurveyManager`, `ScoringEngine`, `EvaluationResult`). `UPPER_SNAKE_CASE` para constantes y enums (`UNDER_EVALUATION`).
- **TypeScript / React (Frontend):** `camelCase` para variables, funciones y hooks (`evaluateProfile`, `userId`, `useSurvey.ts`). `PascalCase` para componentes UI (`SurveyForm.tsx`), interfaces y tipos.
- **PostgreSQL:** Tablas y columnas en `snake_case` (`financial_profile`, `client_id`, `total_score`), valores de estado en `UPPER_SNAKE_CASE` (`'DRAFT'`, `'COMPLETED'`).
- **Frontera JSON (API REST):** Los payloads JSON utilizan `camelCase` (`surveyId`, `totalScore`), convertidos automáticamente en FastAPI heredando de `CamelCaseSchema` (`alias_generator=to_camel`, `populate_by_name=True`, `from_attributes=True`).

### 4.2 Equivalencia directa entre Diagramas UML y Python
*Firmas según los contratos `CT-01`..`CT-12` (v1.1), ya reflejadas en los diagramas de clases del `01` v1.2 (§5.4).*
- UML `evaluateProfile(userId, surveyId, answers)` $\rightarrow$ Python `evaluate_profile(self, user_id: UUID, survey_id: UUID, answers: list[ScoredAnswerDTO]) -> EvaluationResult`
- UML `calculateScore(answers)` $\rightarrow$ Python `calculate_score(self, answers: list[ScoredAnswerDTO]) -> Decimal`
- UML `determineCategory(score)` $\rightarrow$ Python `determine_category(self, score: Decimal) -> FinancialCategory`
- UML `findDraftByUserId(userId)` $\rightarrow$ Python `find_draft_by_user_id(self, user_id: UUID) -> Survey | None`
- UML `findById(surveyId, userId)` $\rightarrow$ Python `find_by_id(self, survey_id: UUID, user_id: UUID) -> Survey | None`
- UML `save(survey)` $\rightarrow$ Python `save(self, survey: Survey) -> Survey | None` (`None` si la transición condicional `DRAFT → COMPLETED` afecta 0 filas)
- UML `saveAnswer(surveyId, userId, answer)` (repositorio) $\rightarrow$ Python `save_answer(self, survey_id: UUID, user_id: UUID, answer: Answer) -> bool`
- UML `saveCategory(userId, evaluation)` $\rightarrow$ Python `save_category(self, user_id: UUID, evaluation: ProfileEvaluation) -> FinancialProfile`

### 4.3 Límites Cuantitativos y Calidad
- **Longitud máxima de línea:** 88 caracteres en Python (`Ruff`) / 100 caracteres en TypeScript (`Prettier`).
- **Longitud máxima de función:** 35 líneas efectivas (sin contar docstring).
- **Parámetros por función:** Máximo 4 (agrupar en DTO/Schema si se requieren más).
- **Complejidad ciclomática:** Máximo 10 (`Ruff C901`).
- **Anidamiento máximo:** 3 niveles (uso obligatorio de *Early Return* / cláusulas de guarda).
- **Pruebas (`pytest` / `Vitest`):** Nomenclatura `test_<operacion>_when_<condicion>_then_<resultado_esperado>` y estructura visual **AAA (Arrange - Act - Assert)**.

### 4.4 Ley de Dirección de Capas
$$\text{router} \longrightarrow \text{service} \longrightarrow \begin{cases} \text{engine} \\ \text{repository} \longrightarrow \text{models} \end{cases}$$
- `router.py` solo maneja HTTP, extrae `user_id` autenticado y traduce excepciones de dominio a códigos HTTP. Prohibido incluir consultas ORM o lógica.
- `service.py` orquesta casos de uso y maneja tolerancia a fallos. Prohibido importar `HTTPException` de FastAPI.
- `engine.py` ejecuta matemática pura en memoria con `Decimal`. Prohibido tocar base de datos o librerías web.
- `repository.py` encapsula SQLAlchemy filtrando siempre por `user_id` (`WHERE client_id = :user_id`).

---

## 5. Diseño de Datos y Contratos (`02_Interaction_and_Data_Design.md` y `docs/contracts/`)

### 5.1 Esquema Relacional en PostgreSQL
1. **`client`:**
   - `client_id` (UUID, PK — corresponde a `user_id` en Python y `userId` en UML/API), `email` (VARCHAR, UNIQUE, NOT NULL), `created_at` (TIMESTAMP).
2. **`survey`:**
   - `survey_id` (UUID, PK), `client_id` (UUID, FK $\rightarrow$ `client`), `status` (VARCHAR: `'DRAFT'`, `'COMPLETED'`), `started_at`, `completed_at` (nullable), `updated_at`.
   - *Restricciones:* Índice único parcial sobre `(client_id) WHERE status = 'DRAFT'` (máximo un borrador abierto por cliente, `BR-02`).
3. **`question`:**
   - `question_id` (INT, PK), `text` (VARCHAR, NOT NULL), `weight` (NUMERIC, NOT NULL, $\ge 0$), `display_order` (INT, UNIQUE en catálogo activo), `is_required` (BOOLEAN), `is_active` (BOOLEAN).
   - *Restricciones:* Máximo 10 preguntas activas (`BR-01`).
4. **`question_option`:**
   - `id` (INT, PK), `question_id` (INT, FK $\rightarrow$ `question.question_id`, `ON DELETE CASCADE`), `option_number` (INT, $> 0$, NOT NULL), `text` (VARCHAR, NOT NULL), `value` (NUMERIC, NOT NULL).
   - *Restricciones:* `UNIQUE (question_id, option_number)`. `value` solo lo usa el backend (oculto en `CT-01`).
5. **`answer`:**
   - `answer_id` (UUID, PK), `survey_id` (UUID, FK $\rightarrow$ `survey`), `question_id` (INT, FK $\rightarrow$ `question`), `selected_option` (INT, $> 0$), `option_value` (NUMERIC, NOT NULL).
   - *Restricciones:* Restricción `UNIQUE (survey_id, question_id)`. `selected_option` se valida contra `question_option (question_id, option_number)` y `option_value` se resuelve desde `question_option.value`.
6. **`financial_profile`:**
   - `profile_id` (UUID, PK), `client_id` (UUID, FK $\rightarrow$ `client`, UNIQUE), `survey_id` (UUID, FK $\rightarrow$ `survey`, NOT NULL), `assigned_category` (VARCHAR: `'CONSERVATIVE'`, `'MODERATE'`, `'AGGRESSIVE'`, `'UNDER_EVALUATION'`), `evaluation_status` (VARCHAR: `'COMPLETED'`, `'ERROR'`), `total_score` (NUMERIC, NULLABLE), `assigned_at` (TIMESTAMP).
   - *Restricciones:* Relación 0..1 por cliente (se actualiza mediante *upsert* por `client_id`, `BR-04`). Si `evaluation_status = 'ERROR'`, entonces `assigned_category = 'UNDER_EVALUATION'` y `total_score IS NULL` (`BR-06`). Se recomienda reforzar esta coherencia con una restricción `CHECK` (`CT-12`).

### 5.2 Contrato de Interfaz Clave: `evaluateProfile` (`CT-10`)
- **Operación:** `CategorizationService.evaluate_profile(user_id: UUID, survey_id: UUID, answers: list[ScoredAnswerDTO]) -> EvaluationResult`. `ScoredAnswerDTO` lleva `question_id`, `option_value` y `weight` (`Decimal`), construido por `SurveyManager` desde las respuestas persistidas.
- **Precondiciones:** Invocada desde `SurveyManager.complete_survey` tras haber confirmado la encuesta como `COMPLETED` (`BR-03`). `user_id` es dueño de `survey_id`.
- **Postcondiciones (Éxito):** Calcula puntaje exacto en `ScoringEngine`, aplica `BR-05`, guarda en `financial_profile` mediante `save_category(user_id, ProfileEvaluation(...))` con estado `'COMPLETED'` (`BR-04`) y retorna `EvaluationResult(survey_id, assigned_category, evaluation_status=COMPLETED, total_score)`.
- **Manejo de Fallos (Escenario 3):** Si `answers` está vacía, lanza `InvalidInputError` sin tocar el perfil. Si ocurre cualquier excepción en cálculo o persistencia definitiva, registra log técnico seguro (`log_error`, sin PII ni respuestas), persiste perfil provisional con `UNDER_EVALUATION` y estado `'ERROR'` (`BR-06`) y retorna `EvaluationResult(survey_id, UNDER_EVALUATION, evaluation_status=ERROR, total_score=None)`. Si también falla la escritura provisional, propaga `EvaluationPersistenceError`.
- **Invariante de coherencia:** `evaluation_status = ERROR` ⇔ `assigned_category = UNDER_EVALUATION` ⇔ `total_score is None`.

### 5.3 Índice de Contratos de Interfaz (`docs/contracts/`, v1.2 — Aprobados 2026-11-12)

Cada contrato sigue Diseño por Contrato: encabezado de trazabilidad, precondiciones, validaciones del proveedor, postcondiciones, invariantes, efectos secundarios, tabla de resultados de fallo y estructura `.json`. Los contratos HTTP incluyen además un fragmento OpenAPI.

| ID | Operación | Capa | HTTP (propuesta) | Reglas |
| :--- | :--- | :--- | :--- | :--- |
| `CT-01` | `startSurvey` | HTTP (`SurveyRouter`) | `POST /api/surveys` → 200 | `BR-01`, `BR-02` |
| `CT-02` | `getCurrentUser` | Auth Dependency | — (401 uniforme) | Riesgo / NFR seguridad |
| `CT-03` | `SurveyManager.startSurvey` | Servicio | — | `BR-01`, `BR-02` |
| `CT-04` | `SurveyRepository.findDraftByUserId` | Repositorio | — | `BR-02` |
| `CT-05` | `SurveyRepository.save` | Repositorio | — | `BR-02`, `BR-03` |
| `CT-06` | `saveAnswer` | HTTP + Servicio | `PUT /api/surveys/{surveyId}/answers` → 204 | `BR-01`..`BR-03` |
| `CT-07` | `SurveyRepository.findById` | Repositorio | — (`null` → 404, nunca 403) | Riesgo / `BR-03` |
| `CT-08` | `SurveyRepository.saveAnswer` | Repositorio | — | `BR-03` |
| `CT-09` | `completeSurvey` | HTTP + Servicio | `POST /api/surveys/{surveyId}/complete` → 200 | `BR-03`..`BR-06` |
| `CT-10` | `CategorizationService.evaluateProfile` | Servicio | — | `BR-04`..`BR-06` |
| `CT-11` | `ScoringEngine.calculateScore` / `determineCategory` | Motor de dominio | — | `BR-05`, NFR precisión |
| `CT-12` | `ProfileRepository.saveCategory` | Repositorio | — | `BR-04`, `BR-06` |

**Decisiones clave incorporadas en los contratos:**
- **Concurrencia (`BR-03`):** el cierre es un `UPDATE … WHERE status = 'DRAFT'` atómico (`CT-05`) y `save_answer` vuelve a comprobar `DRAFT` bajo `SELECT … FOR UPDATE` (`CT-08`); 0 filas → `InvalidStateError` (409).
- **Errores HTTP y formato estándar del cuerpo:** `401` (`UnauthorizedError`), `404` (`NotFoundError`, nunca `403`), `409` (`InvalidStateError`), `422` (`ValidationError` o validación Pydantic), `503` propuesto para `EvaluationPersistenceError`.
  - Respuestas `401`, `404`, `409`, `422` de dominio y `503`: `{ "detail": "<mensaje>" }` (estándar FastAPI).
  - Respuestas `422` de validación estructural Pydantic (`RequestValidationError`): `{ "detail": [{ "type": "string", "loc": ["body", "campo"], "msg": "string" }] }`.
- **Autenticación provisional en Fase 0 (`CT-02`):** mientras no exista servicio emisor de tokens, `get_current_user` en `ENVIRONMENT=development` valida `Authorization: Bearer <token>` aceptando `dev-user-1` (`00000000-0000-0000-0000-000000000001`), `dev-user-2` (`00000000-0000-0000-0000-000000000002`) o un `<client_uuid>` válido existente en `client` (y `X-User-Id` como respaldo opcional si `ALLOW_DEV_USER_HEADER=true`). Cualquier credencial ausente, inválida o inexistente retorna `401` `{ "detail": "No autenticado" }`.
- **`BR-06` en la API:** `completeSurvey` responde 200 también con `evaluationStatus = ERROR`; `totalScore` viaja como `string | null`.
- **Ocultamiento de información:** el DTO de pregunta hacia la `Web App` no expone `weight` ni `question_option.value`; incluye `options` (`id`, `optionNumber`, `text`), `isRequired` y `displayOrder`, y `startSurvey` devuelve las `answers` ya guardadas para reanudar.
- **Pesos:** se toman de `question.weight` y viajan en `ScoredAnswerDTO`; `ScoringEngine` solo guarda los umbrales.

### 5.4 Alineación entre Contratos y Diseños `01` / `02` (Completada 2026-11-12)

Los cambios introducidos por los contratos v1.1 quedaron reflejados en `01` v1.2 y `02` v1.3 (registrados en `02` §4, cambios 6–10). Las secciones "Notas de alineación" de cada contrato se conservan como registro y están marcadas como resueltas:
- [x] `01` §3.2: enum `EvaluationStatus { COMPLETED, ERROR }`; `EvaluationResult.evaluationStatus`; `totalScore : Optional~Decimal~`.
- [x] `01` §3.2: retornos `Optional~Survey~` en `findById`, `findDraftByUserId` y `save`; `SurveyRepository.saveAnswer` → `Boolean`.
- [x] `01` §3.2: `saveCategory(userId, evaluation : ProfileEvaluation) FinancialProfile` (incluye `totalScore`).
- [x] `01` §3.2: `evaluateProfile` y `calculateScore` reciben `List~ScoredAnswerDTO~`; `ScoringEngine.weightMatrix` sustituido por `conservativeThreshold` / `moderateThreshold`.
- [x] `01` §3.2: atributos `Survey.answers`, `startedAt`, `completedAt`; `Question.displayOrder`, `isRequired`, `options`; nueva clase `AnswerOption`.
- [x] `01` §3.3–3.4 y §6: responsabilidades, pseudocódigo de `evaluateProfile` y trazabilidad actualizados.
- [x] `02` §1.1, §2.3–2.5, §3.1–3.2 y §4–5: mensajes `saveCategory(userId, ProfileEvaluation(...))`, `evaluationStatus`, `ScoredAnswerDTO`, estrategia de concurrencia con re-verificación de `DRAFT` y referencias a `CT-XX`.
- [x] **Resuelto (Fase 0 — 2026-11-12):** tabla física del catálogo de opciones `question_option (id, question_id, option_number, text, value)` añadida al modelo ER de `02` §2.2 y alineada en `CT-01` y `CT-06`.

---

## 6. Hoja de Ruta y Checklist de Ejecución (`ADR-0002`)

### [x] Etapa Previa: Ingeniería de Requerimientos y Diseño (Completada — contratos y diseños alineados)
- [x] Especificación de requerimiento Capstone `REQ-01` (User Story, Criterios Gherkin, Caso de Uso y Diagrama de Flujo).
- [x] **Bitácora `2026-11-12` (Bloque 1 — `REQ-01`):** Alineación integral de `docs/req/REQ-01.md` con `02_Interaction_and_Data_Design.md` y `docs/code_style.md`, y rediseño atómico de las reglas de negocio (`BR-01` a `BR-06`) ordenadas según el ciclo de vida del caso de uso.
- [x] **Bitácora `2026-11-12` (Bloque 2 — Diseños y Naming):** Sincronización de `01_Architectural_and_Detailed_Design.md` (`v1.1`), `02_Interaction_and_Data_Design.md`, `adr-0002.md` (renombrado desde `adr_0002.md`), `code_style.md`, `estructura_repositorio.md` y `project_status.md` con `BR-01`..`BR-06`, `saveAnswer`/`save_answer`, `SurveyStatus` `{DRAFT, COMPLETED}`, excepciones unificadas y tablas PostgreSQL en `snake_case`. Clarificación de `CategorizationService` con estereotipo `<<external>>` en el Diagrama B y estandarización del encabezado de trazabilidad a `Scenario / Rule / Constraint`.
- [x] **Bitácora `2026-11-12` (Bloque 3 — Contratos de Interfaz):** Auditoría de los contratos `CT-01`..`CT-12` frente a `REQ-01`, `01`, `02` y `code_style.md` (21 hallazgos: 3 críticos, 6 altos, 8 medios, 4 bajos) y reescritura de los 12 archivos de `docs/contracts/` con encabezado de trazabilidad, resultados de fallo, soporte de `BR-06`, comprobaciones atómicas de estado contra `BR-03` y fragmentos OpenAPI (ver §5.3). 
- [x] **Bitácora `2026-11-12` (Bloque 4 — Alineación de Diseños):** `01_Architectural_and_Detailed_Design.md` → v1.2 y `02_Interaction_and_Data_Design.md` → v1.3, alineados con los contratos v1.1 (§5.4): `EvaluationStatus`, `ProfileEvaluation`, `ScoredAnswerDTO`, `AnswerOption`, retornos opcionales/booleanos en `SurveyRepository` y estrategia de concurrencia con re-verificación de `DRAFT`.
- [x] `ADR-0001`: Selección del Stack Tecnológico.
- [x] `ADR-0002`: Estrategia Híbrida (*Walking Skeleton* + *Vertical Slices*).
- [x] `01_Architectural_and_Detailed_Design.md`: Diagrama de componentes, diagramas de clases UML (`Survey` y `Categorization`), responsabilidades y análisis de cohesión/acoplamiento.
- [x] `02_Interaction_and_Data_Design.md`: Diagramas de secuencia, modelo Entidad-Relación, tabla de *Data Ownership* y contrato formal de `evaluateProfile`.
- [x] `code_style.md` y `estructura_repositorio.md`.

---

### [ ] Fase 0: Walking Skeleton (En curso — Prioridad Inmediata)
*Objetivo: Dejar operativa toda la tubería tecnológica E2E (Frontend → Backend → PostgreSQL del servidor del profesor) antes de codificar la UI final. Criterio de salida: levantar los contenedores Docker de backend y frontend en la VM, ejecutar migración contra el PostgreSQL del profesor, pasar `pytest` en verde y verificar los contratos `CT-01`, `CT-02`, `CT-06` y `CT-09` desde el arnés HTML plano.*

- [ ] **1. Infraestructura y Base de Datos (PostgreSQL del servidor del profesor + Docker en VM):**
  - [ ] Configurar conexión `DATABASE_URL` hacia el **PostgreSQL del servidor del profesor** (sin contenedor de PostgreSQL local).
  - [ ] Crear `docker-compose.yml` en la raíz **únicamente para levantar el backend y el frontend en la VM**.
  - [ ] Crear `.env.example` y `.gitignore` para Python, Node y entornos locales.
- [ ] **2. Esqueleto de Backend (`backend/`):**
  - [ ] Configurar `backend/pyproject.toml` (dependencias: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg`, `alembic`, `pydantic`, `pydantic-settings`; dev: `pytest`, `ruff`, `mypy`, `httpx`).
  - [ ] Implementar `src/core/config.py`, `src/core/database.py`, `src/core/schemas.py` (`CamelCaseSchema`), `src/core/exceptions.py` (formato `{ "detail": ... }` para `401`, `404`, `409`, `422`) y `src/core/auth_deps.py` (`get_current_user` con regla provisional de Fase 0).
  - [ ] Configurar Alembic (`alembic/`) y ejecutar la migración inicial con las **6 tablas** del modelo ER (`client`, `survey`, `question`, `question_option`, `answer`, `financial_profile`) más la semilla inicial de Fase 0.
  - [ ] Implementar los endpoints mínimos E2E (`POST /api/surveys`, `PUT /api/surveys/{surveyId}/answers`, `POST /api/surveys/{surveyId}/complete`, `GET /api/health`) validando los contratos aprobados.
- [ ] **3. Arnés HTML Plano de Verificación de Contratos (`frontend/`):**
  - [ ] Construir una interfaz simple en **HTML puro / texto sin formato** (sin CSS complejo ni diseño visual) que muestre directamente en pantalla los contratos (`CT-01`, `CT-02`, `CT-06`, `CT-09`) en bloques `<pre>`.
  - [ ] Incluir controles HTML básicos (formularios/botones) para disparar peticiones reales al backend y visualizar código HTTP y JSON crudo devuelto tanto en casos exitosos (`200`, `204`) como en errores (`401`, `404`, `409`, `422`).
  - [ ] Ejecutar `pytest` en verde verificando la tubería E2E y todos los contratos.

---

### [ ] Fase 1: Vertical Slice 1 — Camino Feliz (`REQ-01` Escenario 1 + `BR-01`, `BR-03`, `BR-04`, `BR-05`)
- [ ] Semilla/carga de catálogo de hasta 10 preguntas parametrizadas (`question`) con pesos `Decimal` (`BR-01`).
- [ ] Implementación de `ScoringEngine.calculate_score` y `ScoringEngine.determine_category` (aplicando `BR-05` en umbrales exactos).
- [ ] Implementación de `SurveyManager.start_survey` y `SurveyManager.complete_survey` transicionando a `COMPLETED` (`BR-03`) e invocando `CategorizationService.evaluate_profile`.
- [ ] Implementación de `ProfileRepository.save_category` (upsert sobre `financial_profile`, `BR-04`).
- [ ] Construcción de vistas en React para responder cuestionario completo y visualizar pantalla de confirmación con categoría asignada y resumen derivado del plan.
- [ ] Pruebas unitarias de `ScoringEngine` (casos de borde `BR-05`) y prueba de integración E2E del flujo principal.

---

### [ ] Fase 2: Vertical Slice 2 — Resiliencia y Categoría Provisional (`REQ-01` Escenario 3 + `BR-06`)
- [ ] Implementación del bloque `try/except` en `CategorizationService.evaluate_profile` con logging seguro (`log_error`, sin PII, respuestas ni puntajes).
- [ ] Guardado de contingencia en `financial_profile` con `assigned_category = 'UNDER_EVALUATION'`, `evaluation_status = 'ERROR'` y `total_score = None` (`BR-06`), propagando `EvaluationPersistenceError` ante fallo doble.
- [ ] Adaptación de la vista de resultados en React para mostrar aviso de falla temporal con categoría provisional "En Evaluación" y acceso habilitado al panel principal (sin pantalla de error 500).
- [ ] Pruebas automatizadas inyectando fallos simulados en motor/persistencia para verificar el retorno de `EvaluationResult` en estado `ERROR`.

---

### [ ] Fase 3: Vertical Slice 3 — Abandono y Reanudación de Borrador (`REQ-01` Escenario 2 + `BR-02`, `BR-03`)
- [ ] Implementación de `SurveyManager.save_answer` para guardado progresivo unitario, garantizando que una encuesta `COMPLETED` rechace modificaciones (`InvalidStateError`, `BR-03`).
- [ ] Implementación de `SurveyRepository.find_draft_by_user_id` y `SurveyManager.resume_survey` (`BR-02`), delegando a la `Web App` el cálculo de la primera `question` obligatoria sin respuesta en `answer`.
- [ ] Integración en React para guardado progresivo de respuestas y detección automática de borrador al reingresar, ubicando al usuario en la primera pregunta obligatoria pendiente.
- [ ] Pruebas de integración verificando guardado progresivo, reanudación exacta e inmutabilidad de encuestas cerradas.

---

## 7. Preguntas Abiertas y Supuestos Registrados en Diseño

1. **Valores numéricos exactos de los umbrales de categoría:** `REQ-01` y `BR-05` especifican el comportamiento de desempate en el umbral, pero los valores exactos de corte entre `CONSERVATIVE`, `MODERATE` y `AGGRESSIVE` dependen de definición de producto/finanzas. En el código se parametrizarán en el constructor/configuración de `ScoringEngine` (ej. `conservative_threshold`, `moderate_threshold`).
2. **Catálogo de opciones por pregunta (`selected_option`) — Resuelto (2026-11-12):** Formalizado en `02` §2.2 mediante la tabla `question_option (id, question_id, option_number, text, value)`. `CT-01` expone `{ id, optionNumber, text }` (ocultando `value`) y `CT-06` valida `selectedOption` contra `question_option.option_number` para resolver `answer.option_value`.
3. **Fallo doble en persistencia provisional:** Si en el Escenario 3 también falla la escritura de `UNDER_EVALUATION` en la BD, no se introduce cola de mensajería (descartada por `ADR-0001`). `CT-09` propone responder `503` con mensaje genérico; el código HTTP y la experiencia de usuario requieren decisión del stakeholder.
4. **Autenticación y Resumen del Plan:** El módulo de login/registro no hace parte del alcance de diseño detallado de `REQ-01` (se asume `user_id` provisto por dependencia de contexto), y el resumen del plan en el paso 6 es una vista derivada de la categoría asignada, no un módulo de persistencia independiente. `CT-02` fija la interfaz (credencial → `user_id` o 401) y define el mecanismo provisional de Fase 0 (`Bearer dev-user-1`, `dev-user-2`, `<client_uuid>` y `X-User-Id` opcional en desarrollo).
5. **Operaciones sin contrato propio:** `resumeSurvey` como endpoint independiente (hoy cubierto funcionalmente por `CT-01`, que devuelve las respuestas guardadas) y la consulta del perfil vigente (`CategorizationRouter` / `ProfileRepository.find_by_user_id`). Esta última es necesaria para recuperar el resultado si el cliente pierde la respuesta HTTP de `completeSurvey` (un reintento recibe 409).