# Estado del Proyecto y Memoria de Contexto — Asesor Financiero Personal

| | |
| :--- | :--- |
| **Equipo** | Grupo 5 (`@KevinVerjan`, `@Estebandido-exe`, `@josuarezvi`, `@juacortesva`) |
| **Ubicación** | `docs/project_status.md` |
| **Asignatura** | Ingeniería de Software I — Universidad Nacional de Colombia (UNAL) 2026-II |
| **Última Actualización** | 2026-11-12 |
| **Estado Global** | Diseño, ADRs, infraestructura (`g1-team-5-db`) y contratos (`CT-01`..`CT-12`) alineados / Próxima etapa: **Fase 0 — Walking Skeleton** (`ADR-0002`) |
| **Referencias** | `docs/code_style.md`, `docs/estructura_repositorio.md`, `docs/adr/adr-0001.md` a `adr-0006.md`, `docs/req/REQ-01.md`, `docs/design/01_Architectural_and_Detailed_Design.md`, `docs/design/02_Interaction_and_Data_Design.md`, `docs/contracts/` |

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
| **`ADR-0001`** | **Stack Tecnológico e Infraestructura** | **Frontend:** React + Vite + TypeScript 5+. **Backend:** Python 3.11+ con FastAPI, SQLAlchemy 2.0 y Pydantic v2. **Base de Datos:** servidor PostgreSQL externo del curso (`g1-team-5-db`) conectado vía `DATABASE_URL` en `.env`. **Contenedores:** `docker-compose.yml` y `Dockerfile` solo para backend y frontend en desarrollo y en la VM del curso (`CentOS Stream 10`, directorio `/opt/projects-g1/team-5`). |
| **`ADR-0001` / `code_style.md`** | **Precisión Numérica Estricta (Cero `float`)** | **Prohibido usar `float`** para puntajes, pesos de preguntas, valores de opción o montos. En Python se usa exclusivamente `decimal.Decimal` inicializado desde `str` o `int` (ej. `Decimal("0.15")`). En PostgreSQL se usa `NUMERIC(precision, scale)` con `asdecimal=True`. En TypeScript viajan como `string`. |
| **`ADR-0002`** | **Construcción Híbrida Incremental** | **Fase 0:** *Walking Skeleton* (tubería E2E mínima tras limpiar tablas residuales y `alembic_version` en `g1-team-5-db`). **Fases 1 a 3:** *Vertical Slices* por escenario de `REQ-01`. Prohibido desarrollar por capas horizontales aisladas. |
| **`ADR-0003` / `estructura_repositorio.md`** | **Arquitectura Modular y Data Ownership** | División primaria por módulos de dominio (`survey/`, `categorization/`) y secundaria por capas (`router` $\rightarrow$ `service` $\rightarrow$ `engine`/`repository` $\rightarrow$ `models`). Ningún módulo puede importar `models.py` o `repository.py` de otro módulo; el cruce usa DTOs (`ScoredAnswerDTO`, `EvaluationResult`) y aislamiento por `client_id`. |
| **`ADR-0004`** | **Persistencia Progresiva y Locks** | Guardado unitario por respuesta (`save_answer`) con bloqueo pesimista (`SELECT ... FOR UPDATE`), índice único parcial `(client_id) WHERE status = 'DRAFT'` (`BR-02`) y transición atómica `UPDATE ... WHERE status = 'DRAFT'` al cerrar (`BR-03`). |
| **`ADR-0005`** | **Tolerancia Síncrona a Fallos** | Evaluación síncrona tras confirmar `COMPLETED`; ante falla de cálculo o persistencia definitiva registra `UNDER_EVALUATION` con `evaluation_status = 'ERROR'` y `total_score = null` sin brokers ni colas (`BR-06`), y propaga `EvaluationPersistenceError` en fallo doble. |
| **`ADR-0006`** | **Privacidad, Auth y 404** | El `user_id` (`client_id` en BD) se inyecta vía `Depends(get_current_user)` (nunca del body HTTP). Encuestas inexistentes o ajenas devuelven `404` (nunca `403`). **Prohibido registrar en logs (`logger.error`, `print`) respuestas, puntajes ni PII.** |
| **`BR-01`** | **Acotación del Cuestionario** | La encuesta activa consta de un **máximo de 10 preguntas parametrizadas** en la tabla `question` con peso no negativo. |
| **`BR-02`** | **Unicidad de Borrador (`DRAFT`)** | Un cliente puede tener **a lo sumo un borrador (`DRAFT`) activo** a la vez; al reingresar retoma ese mismo borrador sin perder respuestas previas. |
| **`BR-03`** | **Completitud e Inmutabilidad (`COMPLETED`)** | La encuesta solo pasa a `COMPLETED` con todas las preguntas obligatorias respondidas. Una vez `COMPLETED`, es **inmutable** y rechaza modificaciones (`InvalidStateError`). |
| **`BR-04`** | **Categoría Única Vigente** | Todo cliente que completa la encuesta obtiene exactamente una categoría inicial vigente en `financial_profile` vinculada a la encuesta origen. |
| **`BR-05`** | **Desempate Conservador en Umbral** | Si el puntaje calculado se ubica exactamente en el límite (`<=`) entre dos categorías financieras, `ScoringEngine.determine_category` asigna por defecto la categoría de **menor riesgo** (más conservadora). |
| **`BR-06`** | **Asignación Provisional ante Fallo** | Si falla el cálculo o persistencia al evaluar, **no se lanza HTTP 500** ni se usan colas asíncronas. Se captura el error, se asigna `UNDER_EVALUATION` con `evaluation_status = 'ERROR'` y `total_score = null`, sin reabrir la encuesta `COMPLETED` (y propagando `EvaluationPersistenceError` ante fallo doble). |

---

## 3. Estructura de Directorios (Realidad Actual vs. Arquitectura Objetivo)

### 3.1 Estado Actual en el Repositorio
El repositorio contiene la documentación de ingeniería aprobada, la **infraestructura de despliegue** (PR #22) y el **Walking Skeleton + base de encuesta en `frontend/`**. Aún no existe el código fuente de `backend/src/`:

```text
Grupo-5-Finanzas-Ingesoft_I_UN_2026-II/
├── README.md                                            # Ejecución local y despliegue en la VM
├── .env.example                                         # Plantilla de DATABASE_URL y FRONTEND_PORT (sin credenciales)
├── .gitignore
├── docker-compose.yml                                   # Proyecto team-5: servicios backend y frontend
├── backend/
│   ├── Dockerfile                                       # Imagen Python 3.12 del backend
│   ├── entrypoint.sh                                    # alembic upgrade head (si existe alembic.ini) + uvicorn
│   └── .dockerignore
├── frontend/
│   ├── Dockerfile                                       # Build con Node + nginx
│   ├── nginx.conf                                       # Sirve React y reenvía /api/ al backend
│   ├── .dockerignore
│   ├── .env.example
│   ├── .prettierrc
│   ├── .prettierignore
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── index.css
│       ├── testSetup.ts
│       ├── vite-env.d.ts
│       ├── api/
│       │   ├── generated/.gitkeep
│       │   ├── healthService.ts
│       │   ├── healthService.test.ts
│       │   ├── httpClient.ts
│       │   └── httpClient.test.ts
│       ├── features/
│       │   ├── categorization/
│       │   │   ├── components/CategorySummaryPanel.tsx
│       │   │   └── types.ts
│       │   └── survey/
│       │       ├── api/ (surveyApi.ts, httpSurveyApi.ts, mockSurveyApi.ts, mockSurveyApi.test.ts)
│       │       ├── components/ (QuestionCard.tsx, SurveyProgressBar.tsx, SurveyResultCard.tsx)
│       │       ├── hooks/useSurvey.ts
│       │       ├── pages/ (SurveyView.tsx, SurveyView.test.tsx)
│       │       └── types.ts
│       └── shared/
│           ├── components/ (ConnectivityBanner.tsx, ErrorAlert.tsx)
│           └── utils/ (formatters.ts, formatters.test.ts)
└── docs/
    ├── code_style.md                                    # Estándares Ruff, ESLint, Decimal, Logs
    ├── estructura_repositorio.md                        # Reglas de monorepo y capas
    ├── project_status.md                                # Estado actualizado del proyecto (este archivo)
    ├── adr/
    │   ├── adr-0001.md                                  # Selección del Stack (React, FastAPI, PostgreSQL externo)
    │   ├── adr-0002.md                                  # Estrategia Walking Skeleton + Vertical Slices
    │   ├── adr-0003.md                                  # Partición modular y Data Ownership por client_id
    │   ├── adr-0004.md                                  # Persistencia progresiva, bloqueo pesimista e índice DRAFT
    │   ├── adr-0005.md                                  # Tolerancia síncrona a fallos (UNDER_EVALUATION)
    │   ├── adr-0006.md                                  # Ocultamiento 404, auth server-side y logs sin PII
    │   └── adr-0007.md                                  # Aislamiento de adaptadores API (mock vs HTTP) y fetch nativo
    ├── contracts/
    │   ├── 01-http-start-survey.md                      # CT-01 a CT-12: contratos por operación HTTP/Service/Repo
    │   ├── ...
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
├── .env.example                                         # Plantilla con DATABASE_URL hacia g1-team-5-db (sin credenciales reales)
├── docker-compose.yml                                   # Orquestación exclusiva de backend y frontend (dev y VM CentOS Stream 10: /opt/projects-g1/team-5)
├── docs/                                                # Documentación de Ingeniería (YA EXISTENTE)
│   ├── code_style.md                                    # Estándares Ruff, ESLint, Decimal, Logs
│   ├── estructura_repositorio.md                        # Reglas de monorepo y capas
│   ├── project_status.md                                # Estado actualizado del proyecto
│   ├── adr/
│   │   ├── adr-0001.md
│   │   ├── adr-0002.md
│   │   ├── adr-0003.md
│   │   ├── adr-0004.md
│   │   ├── adr-0005.md
│   │   └── adr-0006.md
│   ├── contracts/                                       # Contratos por operación (CT-01 a CT-12)
│   │   └── 01-http-start-survey.md .. 12-repo-save-category.md
│   ├── design/
│   │   ├── 01_Architectural_and_Detailed_Design.md
│   │   └── 02_Interaction_and_Data_Design.md
│   ├── req/
│   │   └── REQ-01.md
│   └── rfc/
│       └── rfc_proyecto.md
├── backend/                                             # API REST y Lógica de Negocio (POR CONSTRUIR)
│   ├── Dockerfile                                       # Imagen reproducible del backend FastAPI
│   ├── entrypoint.sh                                    # Arranque: migraciones Alembic + uvicorn
│   ├── pyproject.toml                                   # Configuración de dependencias, Ruff, Mypy y Pytest
│   ├── alembic/                                         # Migraciones de esquema sobre PostgreSQL externo (g1-team-5-db)
│   │   └── versions/
│   ├── src/
│   │   ├── main.py                                      # Punto de entrada de FastAPI y registro de routers
│   │   ├── core/                                        # database.py (SQLAlchemy), config.py, auth_deps.py (user_id), schemas.py
│   │   ├── survey/                                      # Módulo Survey (REQ-01)
│   │   │   ├── router.py                                # SurveyRouter (endpoints HTTP)
│   │   │   ├── service.py                               # SurveyManager (ciclo DRAFT/COMPLETED)
│   │   │   ├── repository.py                            # SurveyRepository (contrato + implementación SQLAlchemy)
│   │   │   ├── models.py                                # Tablas survey, question, answer
│   │   │   ├── schemas.py                               # DTOs Pydantic de entrada/salida (CamelCaseSchema)
│   │   │   └── enums.py                                 # SurveyStatus (DRAFT, COMPLETED)
│   │   └── categorization/                              # Módulo Categorization (REQ-01)
│   │       ├── router.py                                # CategorizationRouter
│   │       ├── service.py                               # CategorizationService (orquestación y fallback Escenario 3)
│   │       ├── engine.py                                # ScoringEngine (umbrales Decimal y BR-05 aislados)
│   │       ├── repository.py                            # ProfileRepository (contrato + implementación SQLAlchemy)
│   │       ├── models.py                                # Tabla financial_profile
│   │       ├── schemas.py                               # EvaluationResult, ScoredAnswerDTO, ProfileEvaluation
│   │       └── enums.py                                 # FinancialCategory (...), EvaluationStatus (COMPLETED, ERROR)
│   └── tests/
│       ├── unit/                                        # Ej: test_scoring_engine.py (probar BR-05 sin BD)
│       └── integration/                                 # Ej: test_evaluate_profile.py contra g1-team-5-db (Escenarios 1, 2 y 3)
└── frontend/                                            # Aplicación Web Cliente React + Vite + TS (POR CONSTRUIR)
    ├── Dockerfile                                       # Imagen reproducible del frontend React + Vite
    ├── nginx.conf                                       # Sirve el build y reenvía /api/ al backend
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
- UML `evaluateProfile(userId, surveyId, answers)` $\rightarrow$ Python `evaluate_profile(self, user_id: UUID, survey_id: UUID, answers: list[ScoredAnswerDTO]) -> EvaluationResult`
- UML `calculateScore(answers)` $\rightarrow$ Python `calculate_score(self, answers: list[ScoredAnswerDTO]) -> Decimal`
- UML `determineCategory(score)` $\rightarrow$ Python `determine_category(self, score: Decimal) -> FinancialCategory`
- UML `findDraftByUserId(userId)` $\rightarrow$ Python `find_draft_by_user_id(self, user_id: UUID) -> Survey | None`

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

## 5. Diseño de Datos y Contratos (`02_Interaction_and_Data_Design.md`)

### 5.1 Esquema Relacional en PostgreSQL (`g1-team-5-db`)
1. **`client`:**
   - `client_id` (UUID, PK — corresponde a `user_id` en Python y `userId` en UML/API), `email` (VARCHAR, UNIQUE, NOT NULL), `created_at` (TIMESTAMP).
2. **`survey`:**
   - `survey_id` (UUID, PK), `client_id` (UUID, FK $\rightarrow$ `client`), `status` (VARCHAR: `'DRAFT'`, `'COMPLETED'`), `started_at`, `completed_at` (nullable), `updated_at`.
   - *Restricciones:* Índice único parcial sobre `(client_id) WHERE status = 'DRAFT'` (máximo un borrador abierto por cliente, `BR-02`).
3. **`question`:**
   - `question_id` (INT, PK), `text` (VARCHAR, NOT NULL), `weight` (NUMERIC, NOT NULL, $\ge 0$), `display_order` (INT, UNIQUE en catálogo activo), `is_required` (BOOLEAN), `is_active` (BOOLEAN).
   - *Restricciones:* Máximo 10 preguntas activas (`BR-01`).
4. **`answer`:**
   - `answer_id` (UUID, PK), `survey_id` (UUID, FK $\rightarrow$ `survey`), `question_id` (INT, FK $\rightarrow$ `question`), `selected_option` (INT, $> 0$), `option_value` (NUMERIC, NOT NULL).
   - *Restricciones:* Restricción `UNIQUE (survey_id, question_id)`.
5. **`financial_profile`:**
   - `profile_id` (UUID, PK), `client_id` (UUID, FK $\rightarrow$ `client`, UNIQUE), `survey_id` (UUID, FK $\rightarrow$ `survey`, NOT NULL), `assigned_category` (VARCHAR: `'CONSERVATIVE'`, `'MODERATE'`, `'AGGRESSIVE'`, `'UNDER_EVALUATION'`), `evaluation_status` (VARCHAR: `'COMPLETED'`, `'ERROR'`), `total_score` (NUMERIC, NULLABLE), `assigned_at` (TIMESTAMP).
   - *Restricciones:* Relación 0..1 por cliente (se actualiza mediante *upsert* por `client_id`, `BR-04`). Si `evaluation_status = 'ERROR'`, entonces `assigned_category = 'UNDER_EVALUATION'` y `total_score IS NULL` (`BR-06`).

### 5.2 Contrato de Interfaz Clave: `evaluateProfile` (`CT-10`)
- **Operación:** `CategorizationService.evaluate_profile(user_id: UUID, survey_id: UUID, answers: list[ScoredAnswerDTO]) -> EvaluationResult`
- **Precondiciones:** Invocada desde `SurveyManager.complete_survey` tras haber persistido la encuesta como `COMPLETED` (`BR-03`). `answers` no está vacía y contiene `question_id`, `option_value` y `weight` ya resueltos por `survey`.
- **Postcondiciones (Éxito):** Calcula puntaje exacto en `ScoringEngine`, aplica `BR-05`, guarda `ProfileEvaluation(survey_id, assigned_category, EvaluationStatus.COMPLETED, total_score)` vía `ProfileRepository.save_category` (`BR-04`) y retorna `EvaluationResult(survey_id, assigned_category, EvaluationStatus.COMPLETED, total_score)`.
- **Manejo de Fallos (Escenario 3 / `ADR-0005`):** Si `answers` está vacía, lanza `InvalidInputError` sin tocar el perfil. Si ocurre cualquier excepción en cálculo o persistencia definitiva, registra log técnico seguro (`log_error`, sin PII ni respuestas), persiste perfil provisional con `ProfileEvaluation(survey_id, UNDER_EVALUATION, EvaluationStatus.ERROR, None)` (`BR-06`) y retorna `EvaluationResult(survey_id, UNDER_EVALUATION, EvaluationStatus.ERROR, None)`. Si también falla la escritura provisional, propaga `EvaluationPersistenceError`.
- **Contratos detallados (`CT-01` a `CT-12`):** Disponibles por operación en `docs/contracts/` (`01-http-start-survey.md` a `12-repo-save-category.md`).

---

## 6. Hoja de Ruta y Checklist de Ejecución (`ADR-0002`)

### [x] Etapa Previa: Ingeniería de Requerimientos, Diseño, ADRs y Contratos (100% Completada)
- [x] Especificación de requerimiento Capstone `REQ-01` (User Story, Criterios Gherkin, Caso de Uso y Diagrama de Flujo).
- [x] **Bitácora `2026-11-12` (Bloque 1 — `REQ-01`):** Alineación integral de `docs/req/REQ-01.md` con `02_Interaction_and_Data_Design.md` y `docs/code_style.md`, y rediseño atómico de las reglas de negocio (`BR-01` a `BR-06`) ordenadas según el ciclo de vida del caso de uso.
- [x] **Bitácora `2026-11-12` (Bloque 2 — Diseños y Naming):** Sincronización de `01_Architectural_and_Detailed_Design.md` (`v1.1`), `02_Interaction_and_Data_Design.md`, `adr-0002.md` (renombrado desde `adr_0002.md`), `code_style.md`, `estructura_repositorio.md` y `project_status.md` con `BR-01`..`BR-06`, `saveAnswer`/`save_answer`, `SurveyStatus` `{DRAFT, COMPLETED}`, excepciones unificadas y tablas PostgreSQL en `snake_case`. Clarificación de `CategorizationService` con estereotipo `<<external>>` en el Diagrama B y estandarización del encabezado de trazabilidad a `Scenario / Rule / Constraint`.
- [x] **Bitácora `2026-11-12` (Bloque 3 — Infraestructura, ADRs y Contratos):** Alineación de infraestructura con el servidor PostgreSQL externo del curso (`g1-team-5-db`), contenedores `docker-compose.yml`/`Dockerfile` exclusivos para backend y frontend en la VM `CentOS Stream 10` (`/opt/projects-g1/team-5`), inclusión del saneamiento previo de tablas residuales en `g1-team-5-db` antes de Alembic, formalización de `ADR-0003` a `ADR-0006` (y actualización de `ADR-0001`/`ADR-0002`), y reconciliación de `01`, `02` y `code_style.md` con `docs/contracts/` (`CT-01`..`CT-12`).
- [x] `ADR-0001`: Selección del Stack Tecnológico e Infraestructura (`g1-team-5-db` + Docker backend/frontend).
- [x] `ADR-0002`: Estrategia Híbrida (*Walking Skeleton* + *Vertical Slices*).
- [x] `ADR-0003`: Partición modular por dominio (`survey/`, `categorization/`) y propiedad de datos por `client_id`.
- [x] `ADR-0004`: Persistencia unitaria progresiva, bloqueo pesimista (`SELECT ... FOR UPDATE`) e índice único parcial de borrador.
- [x] `ADR-0005`: Tolerancia síncrona a fallos de evaluación (`UNDER_EVALUATION`) sin brokers de mensajería.
- [x] `ADR-0006`: Ocultamiento de existencia (`404` vs. `403`), inyección server-side de `user_id` y logs sin PII.
- [x] `ADR-0007`: Aislamiento de adaptadores API (`mockSurveyApi` vs `httpSurveyApi`) y cliente `fetch` nativo en frontend.
- [x] `01_Architectural_and_Detailed_Design.md`, `02_Interaction_and_Data_Design.md`, `code_style.md`, `estructura_repositorio.md` y `docs/contracts/` (`CT-01`..`CT-12`).

---

### [ ] Fase 0: Walking Skeleton (En Progreso — Infraestructura y Frontend Base Completados)
*Objetivo: Dejar operativa toda la tubería tecnológica E2E antes de codificar las reglas financieras. Criterio de salida: clonar repo, limpiar la BD externa `g1-team-5-db`, ejecutar migraciones Alembic desde cero, levantar contenedores backend/frontend (`docker-compose.yml`) conectados a `g1-team-5-db` (incluyendo verificación en la VM `CentOS Stream 10`, directorio `/opt/projects-g1/team-5`), ver una petición viajando desde React hasta PostgreSQL y pasar `pytest` en verde.*

- [x] **Bitácora `2026-11-12` (Bloque 4 — Frontend Walking Skeleton y Base de Encuesta):** Inicialización de `frontend/` (React + Vite + TypeScript `strict`), ESLint (`no-explicit-any`, máx. 100 caracteres), Prettier, cliente HTTP (`src/api/httpClient.ts`), banner de conectividad (`/api/health` vs `VITE_USE_MOCK_API`), flujo completo de encuesta sobre contratos `CT-01`, `CT-06` y `CT-09` con adaptador mock aislado (`ADR-0007`) y suite Vitest en verde (5 archivos, 17 pruebas).
- [x] **1. Saneamiento de BD Externa (`g1-team-5-db`) e Infraestructura Docker:**
  - [x] **Prerrequisito obligatorio antes de Alembic** (realizado el 2026-11-13: `g1-team-5-db` quedó sin tablas): Vaciar/limpiar las tablas residuales y `alembic_version` actualmente alojadas en el servidor PostgreSQL externo del curso (`g1-team-5-db`) provenientes de migraciones revertidas en `main`, para ejecutar Alembic desde cero sin conflictos de esquema.
  - [x] Crear `.env.example` (con `DATABASE_URL` apuntando a `g1-team-5-db`, sin credenciales reales) y `.gitignore` para Python, Node y entornos locales.
  - [x] Crear `backend/Dockerfile`, `frontend/Dockerfile` y `docker-compose.yml` en la raíz **exclusivamente** para el backend (FastAPI) y el frontend (React/Vite), permitiendo desarrollo reproducible y despliegue en la VM del curso (`CentOS Stream 10`, directorio `/opt/projects-g1/team-5`) contra `g1-team-5-db`.
- [ ] **2. Esqueleto de Backend (`backend/`):**
  - [ ] Configurar `backend/pyproject.toml` (dependencias: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg`/`asyncpg`, `alembic`, `pydantic`, `pydantic-settings`; dev: `pytest`, `ruff`, `mypy`, `httpx`).
  - [ ] Implementar `src/core/config.py`, `src/core/database.py`, `src/core/schemas.py` (`CamelCaseSchema`) y `src/core/auth_deps.py` (dependencia de `user_id`).
  - [ ] Configurar Alembic (`alembic/`) y generar la migración inicial sobre `g1-team-5-db` limpia con las 5 tablas del modelo ER (`client`, `survey`, `question`, `answer`, `financial_profile`).
  - [ ] Crear estructura base de paquetes en `src/survey/` y `src/categorization/` junto con un endpoint de conectividad E2E en `src/main.py`.
- [ ] **3. Contrato OpenAPI y Esqueleto de Frontend (`frontend/`):**
  - [x] Inicializar aplicación React + Vite + TypeScript en `frontend/` con cliente HTTP (`httpClient.ts`), indicador `/api/health` y base de encuesta (`CT-01`, `CT-06`, `CT-09`) con adaptador mock/HTTP y pruebas Vitest en verde.
  - [x] Configurar script `generate:api` (`openapi-typescript`) en `package.json` para exportar esquemas de FastAPI a `frontend/src/api/generated/`.
  - [ ] Conectar pantalla base en React consumiendo el backend real (`VITE_USE_MOCK_API=false`) y ejecutar primera prueba E2E en verde con `pytest`.

---

### [ ] Fase 1: Vertical Slice 1 — Camino Feliz (`REQ-01` Escenario 1 + `BR-01`, `BR-03`, `BR-04`, `BR-05`)
- [ ] Semilla/carga de catálogo de hasta 10 preguntas parametrizadas (`question`) con pesos `Decimal` (`BR-01`).
- [ ] Implementación de `ScoringEngine.calculate_score` y `ScoringEngine.determine_category` (aplicando `BR-05` en umbrales exactos).
- [ ] Implementación de `SurveyManager.start_survey` y `SurveyManager.complete_survey` transicionando a `COMPLETED` (`BR-03`), construyendo `list[ScoredAnswerDTO]` e invocando `CategorizationService.evaluate_profile`.
- [ ] Implementación de `ProfileRepository.save_category` (upsert sobre `financial_profile` con `ProfileEvaluation`, `BR-04`).
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
- [ ] Implementación de `SurveyManager.save_answer` para guardado progresivo unitario, garantizando que una encuesta `COMPLETED` rechace modificaciones (`InvalidStateError`, `BR-03`) bajo bloqueo pesimista (`ADR-0004`).
- [ ] Implementación de `SurveyRepository.find_draft_by_user_id` y `SurveyManager.resume_survey` (`BR-02`), delegando a la `Web App` el cálculo de la primera `question` obligatoria sin respuesta en `answer`.
- [ ] Integración en React para guardado progresivo de respuestas y detección automática de borrador al reingresar, ubicando al usuario en la primera pregunta obligatoria pendiente.
- [ ] Pruebas de integración verificando guardado progresivo, reanudación exacta e inmutabilidad de encuestas cerradas.

---

## 7. Preguntas Abiertas y Supuestos Registrados en Diseño

1. **Valores numéricos exactos de los umbrales de categoría:** `REQ-01` y `BR-05` especifican el comportamiento de desempate en el umbral, pero los valores exactos de corte entre `CONSERVATIVE`, `MODERATE` y `AGGRESSIVE` dependen de definición de producto/finanzas. En el código se parametrizarán en el constructor/configuración de `ScoringEngine` (ej. `conservative_threshold`, `moderate_threshold`).
2. **Catálogo de opciones por pregunta (`selected_option`):** Se modela como entero positivo con `option_value` (`Decimal`) resuelto. Falta acordar el catálogo físico de opciones válidas por pregunta (`CT-03` / `CT-08`).
3. **Fallo doble en persistencia provisional y recuperación HTTP:** Si en el Escenario 3 también falla la escritura de `UNDER_EVALUATION` en la BD, no se introduce cola de mensajería (`ADR-0001`, `ADR-0005`). Queda pendiente confirmar el mapeo HTTP propuesto para `EvaluationPersistenceError` (`503 Service Unavailable` en `CT-09`) y el contrato de consulta del perfil (`CategorizationRouter` / `ProfileRepository.find_by_user_id`) para recuperación si se pierde la respuesta HTTP de `completeSurvey`.
4. **Autenticación y Resumen del Plan:** El módulo de login/registro no hace parte del alcance de diseño detallado de `REQ-01` (se asume `user_id` provisto por `Depends(get_current_user)` según `ADR-0006`), y el resumen del plan en el paso 6 es una vista derivada de la categoría asignada, no un módulo de persistencia independiente.