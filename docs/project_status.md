# Estado del Proyecto y Memoria de Contexto — Asesor Financiero Personal

| | |
| :--- | :--- |
| **Equipo** | Grupo 5 (`@KevinVerjan`, `@Estebandido-exe`, `@josuarezvi`, `@juacortesva`) |
| **Ubicación** | `docs/project_status.md` |
| **Asignatura** | Ingeniería de Software I — Universidad Nacional de Colombia (UNAL) 2026-II |
| **Última Actualización** | 2026-11-12 |
| **Estado Global** | **Fase 0 — Walking Skeleton** completada en `feat/walking-skeleton-db` (pendiente de *merge* y despliegue en la VM) / Próxima etapa: **Slice 1** |
| **Referencias** | `docs/code_style.md`, `docs/estructura_repositorio.md`, `docs/adr/adr-0001.md`, `docs/adr/adr_0002.md`, `docs/req/REQ-01.md`, `docs/design/01_Architectural_and_Detailed_Design.md`, `docs/design/02_Interaction_and_Data_Design.md` |

---

## 1. Propósito de este Documento (Instrucciones para la IA)

Este archivo actúa como la **Fuente Única de Verdad (Single Source of Truth)** sobre el estado actual del repositorio, las decisiones de arquitectura aprobadas, las reglas de negocio y el plan de trabajo incremental del proyecto **Asesor Financiero Personal**.

Cualquier asistente de IA que reciba este documento debe:
1. **Respetar estrictamente la arquitectura, capas y convenciones** aquí descritas sin inventar módulos, colas de mensajes (brokers) ni tecnologías fuera del stack aprobado en `ADR-0001`.
2. **Distinguir entre lo que ya existe en el repositorio (Sección 3.1) y lo que está pendiente de construir (Sección 3.2 y Sección 7)**.
3. **Aplicar todas las restricciones de código de `docs/code_style.md`** (tipado estricto, aritmética `Decimal`, privacidad en logs y límites de complejidad).

---

## 2. Resumen del Sistema y Reglas Inmutables

### 2.1 Propósito del Sistema (`REQ-01`)
Aplicación web interactiva que permite a los usuarios descubrir y registrar su perfil financiero mediante una encuesta breve de *onboarding* (máximo 10 preguntas, menos de 3 minutos), evaluando sus respuestas contra una matriz de ponderación para asignar una categoría de inicio (`CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`) que personalice su plan financiero.

### 2.2 Matriz de Decisiones Arquitectónicas y Reglas de Negocio

| Identificador | Regla / Decisión | Restricción Técnica Obligatoria |
| :--- | :--- | :--- |
| **`ADR-0001`** | **Stack Tecnológico Políglota** | **Frontend:** React + Vite + TypeScript 5+. **Backend:** Python 3.11+ con FastAPI, SQLAlchemy 2.0 y Pydantic v2. **Base de Datos:** PostgreSQL. |
| **`ADR-0001` / `code_style.md`** | **Precisión Numérica Estricta (Cero `float`)** | **Prohibido usar `float`** para puntajes, pesos de preguntas, valores de opción o montos.En Python se usa exclusivamente `decimal.Decimal` inicializado desde `str` o `int` (ej. `Decimal("0.15")`). En PostgreSQL se usa `NUMERIC(precision, scale)` con `asdecimal=True`. En TypeScript viajan como `string`. |
| **`ADR-0002`** | **Construcción Híbrida Incremental** | **Fase 0:** *Walking Skeleton* (tubería E2E mínima). **Fases 1 a 3:** *Vertical Slices* por escenario de `REQ-01`. Prohibido desarrollar por capas horizontales aisladas. |
| **`estructura_repositorio.md`** | **Arquitectura Modular y Data Ownership** | División primaria por módulos de dominio (`survey/`, `categorization/`) y secundaria por capas (`router` $\rightarrow$ `service` $\rightarrow$ `engine`/`repository` $\rightarrow$ `models`). Ningún módulo puede importar `models.py` o `repository.py` de otro módulo. |
| **`BR-01`** | **Categoría Previa al Plan** | Todo cliente registrado debe tener una categoría inicial asignada en `FINANCIAL_PROFILE` antes de visualizar recomendaciones. |
| **`BR-02`** | **Acotación de la Encuesta** | El cuestionario está limitado a un **máximo de 10 preguntas activas** en la tabla `QUESTION`. |
| **`BR-03`** | **Desempate Conservador en Umbral** | Si el puntaje calculado se ubica exactamente en el límite (`<=`) entre dos categorías financieras, `ScoringEngine.determine_category` asigna por defecto la categoría de **menor riesgo** (más conservadora). |
| **`REQ-01` (Escenario 2)** | **Borrador Único e Inmutabilidad** | Un cliente puede tener **a lo sumo un borrador (`DRAFT`) activo** a la vez. Una vez que una encuesta pasa a estado `COMPLETED`, es **inmutable** y rechaza cualquier invocación a `save_draft`. |
| **`REQ-01` (Escenario 3)** | **Tolerancia a Fallos Síncrona** | Si falla el motor de cálculo o la persistencia al evaluar, **no se lanza HTTP 500** ni se usan colas asíncronas (RabbitMQ/Celery rechazados en `ADR-0001`). Se captura el error, se asigna la categoría provisional `UNDER_EVALUATION` con `evaluation_status = 'ERROR'` y `total_score = null`, permitiendo el paso al panel principal. |
| **Seguridad y Privacidad** | **Protección de Datos y Logs (`REQ-01`)** | El `user_id` se extrae siempre de la dependencia de autenticación del backend, nunca del body HTTP. **Prohibido registrar en logs (`logger.error`, `print`) las respuestas (`answers`), puntajes (`total_score`) o datos personales del usuario.** |

---

## 3. Estructura de Directorios (Realidad Actual vs. Arquitectura Objetivo)

### 3.1 Estado Actual en el Repositorio (`feat/walking-skeleton-db`)
La rama del *Walking Skeleton* agrega `backend/`, `frontend/` y `docker-compose.yml` sobre la documentación existente:

```text
Grupo-5-Finanzas-Ingesoft_I_UN_2026-II/
├── README.md                                            # Arranque local y despliegue en la VM
├── docker-compose.yml                                   # PostgreSQL 16 local (volumen + healthcheck)
├── docs/                                                # Sin cambios de estructura (ver 3.2)
├── backend/
│   ├── .env.example                                     # DATABASE_URL genérica, CORS_ORIGINS, DEMO_MODE
│   ├── pyproject.toml                                   # build-system, Ruff, Mypy strict, Pytest
│   ├── alembic/versions/
│   │   ├── 8cedce29f65b_create_initial_schema_for_req_01.py   # 5 tablas del modelo ER
│   │   └── e4a1ef71cbd4_add_design_constraints_for_req_01.py  # CHECKs + display_order único activo
│   ├── scripts/
│   │   ├── seed_demo.py                                 # Cliente demo + 3 preguntas (idempotente)
│   │   └── smoke_test.sh                                # Prueba de humo por CLI (curl)
│   ├── src/
│   │   ├── main.py                                      # CORS desde Settings, /api/v1/health con SELECT 1
│   │   ├── core/                                        # config, database, auth_deps, schemas, models (ClientModel)
│   │   ├── survey/                                      # router, service, repository, models, schemas, enums
│   │   └── categorization/                              # models (FinancialProfileModel), enums
│   └── tests/
│       ├── conftest.py                                  # Transacción con rollback por prueba
│       ├── unit/test_config.py
│       └── integration/test_walking_skeleton.py         # E2E + invariantes de BD
└── frontend/                                            # React + Vite + TS estricto, sin estilos
    ├── package.json                                     # Script gen:api (openapi-typescript)
    └── src/
        ├── api/client.ts + api/generated/schema.d.ts    # Tipos generados desde /openapi.json
        ├── shared/hooks/                                # useAsyncAction, useHealth
        └── features/survey/                             # hooks/useSurveyStart, pages/SkeletonCheckPage
```

### 3.2 Árbol Objetivo Completo del Monorepo (Integrando `docs/` Existente + Código por Construir)
Esta es la estructura completa hacia la cual evolucionará el repositorio durante las Fases 0 a 3, conservando intacta la carpeta `docs/`:

```text
Grupo-5-Finanzas-Ingesoft_I_UN_2026-II/
├── README.md                                            # Descripción general e instrucciones de arranque
├── docker-compose.yml                                   # Para levantar PostgreSQL local rápido
├── docs/                                                # Documentación de Ingeniería (YA EXISTENTE)
│   ├── code_style.md                                    # Estándares Ruff, ESLint, Decimal, Logs
│   ├── estructura_repositorio.md                        # Reglas de monorepo y capas
│   ├── project_status.md                                # Estado actualizado del proyecto
│   ├── adr/
│   │   ├── adr-0001.md
│   │   └── adr_0002.md
│   ├── design/
│   │   ├── 01_Architectural_and_Detailed_Design.md
│   │   └── 02_Interaction_and_Data_Design.md
│   ├── req/
│   │   ├── REQ-01.md
│   │   └── REQ-02.md
│   └── rfc/
│       └── rfc_proyecto.md
├── backend/                                             # API REST y Lógica de Negocio (POR CONSTRUIR)
│   ├── pyproject.toml                                   # Configuración de dependencias, Ruff, Mypy y Pytest
│   ├── alembic/                                         # Migraciones de esquema de PostgreSQL
│   │   └── versions/
│   ├── src/
│   │   ├── main.py                                      # Punto de entrada de FastAPI y registro de routers
│   │   ├── core/                                        # database.py (SQLAlchemy), config.py, auth_deps.py (userId), schemas.py
│   │   ├── survey/                                      # Módulo Survey (REQ-01)
│   │   │   ├── router.py                                # Survey Router (endpoints HTTP)
│   │   │   ├── service.py                               # SurveyManager (ciclo DRAFT/COMPLETED)
│   │   │   ├── repository.py                            # ISurveyRepository + implementación SQLAlchemy
│   │   │   ├── models.py                                # Tablas SURVEY, QUESTION, ANSWER
│   │   │   ├── schemas.py                               # DTOs Pydantic de entrada/salida (CamelCaseSchema)
│   │   │   └── enums.py                                 # SurveyStatus (DRAFT, COMPLETED); ERROR vive en evaluation_status
│   │   └── categorization/                              # Módulo Categorization (REQ-01)
│   │       ├── router.py                                # Categorization Router
│   │       ├── service.py                               # CategorizationService (orquestación y fallback Escenario 3)
│   │       ├── engine.py                                # ScoringEngine (matriz Decimal y BR-03 aislados)
│   │       ├── repository.py                            # IProfileRepository + implementación SQLAlchemy
│   │       ├── models.py                                # Tabla FINANCIAL_PROFILE
│   │       ├── schemas.py                               # EvaluationResult
│   │       └── enums.py                                 # FinancialCategory (CONSERVATIVE, MODERATE, AGGRESSIVE, UNDER_EVALUATION)
│   └── tests/
│       ├── unit/                                        # Ej: test_scoring_engine.py (probar BR-03 sin BD)
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
- **Python (Backend):** `snake_case` para funciones, métodos, variables y módulos (`evaluate_profile`, `user_id`, `scoring_engine.py`). `PascalCase` para clases, modelos y schemas (`SurveyManager`, `ScoringEngine`, `EvaluationResult`). `UPPER_SNAKE_CASE` para constantes y enums (`UNDER_EVALUATION`).
- **TypeScript / React (Frontend):** `camelCase` para variables, funciones y hooks (`evaluateProfile`, `userId`, `useSurvey.ts`). `PascalCase` para componentes UI (`SurveyForm.tsx`), interfaces y tipos.
- **PostgreSQL:** Tablas y columnas en `snake_case` (`financial_profile`, `client_id`, `total_score`), valores de estado en `UPPER_SNAKE_CASE` (`'DRAFT'`, `'COMPLETED'`).
- **Frontera JSON (API REST):** Los payloads JSON utilizan `camelCase` (`surveyId`, `totalScore`), convertidos automáticamente en FastAPI heredando de `CamelCaseSchema` (`alias_generator=to_camel`, `populate_by_name=True`, `from_attributes=True`).

### 4.2 Equivalencia directa entre Diagramas UML y Python
- UML `evaluateProfile(userId, surveyId, answers)` $\rightarrow$ Python `evaluate_profile(self, user_id: UUID, survey_id: UUID, answers: list[Answer]) -> EvaluationResult`
- UML `calculateScore(answers)` $\rightarrow$ Python `calculate_score(self, answers: list[Answer]) -> Decimal`
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
- `repository.py` encapsula SQLAlchemy filtrando siempre por `user_id`.

---

## 5. Diseño de Datos y Contratos (`02_Interaction_and_Data_Design.md`)

### 5.1 Esquema Relacional en PostgreSQL
1. **`CLIENT`:**
   - `client_id` (UUID, PK), `email` (VARCHAR, UNIQUE, NOT NULL), `created_at` (TIMESTAMP).
2. **`SURVEY`:**
   - `survey_id` (UUID, PK), `client_id` (UUID, FK $\rightarrow$ `CLIENT`), `status` (VARCHAR: `'DRAFT'`, `'COMPLETED'`), `started_at`, `completed_at` (nullable), `updated_at`.
   - *Restricciones:* Índice único parcial sobre `(client_id) WHERE status = 'DRAFT'` (máximo un borrador abierto por cliente).
3. **`QUESTION`:**
   - `question_id` (INT, PK), `text` (VARCHAR, NOT NULL), `weight` (NUMERIC, NOT NULL, $\ge 0$), `display_order` (INT, UNIQUE), `is_required` (BOOLEAN).
   - *Restricciones:* Máximo 10 preguntas activas (`BR-02`).
4. **`ANSWER`:**
   - `answer_id` (UUID, PK), `survey_id` (UUID, FK $\rightarrow$ `SURVEY`), `question_id` (INT, FK $\rightarrow$ `QUESTION`), `selected_option` (INT, $> 0$), `option_value` (NUMERIC, NOT NULL).
   - *Restricciones:* Restricción `UNIQUE (survey_id, question_id)`.
5. **`FINANCIAL_PROFILE`:**
   - `profile_id` (UUID, PK), `client_id` (UUID, FK $\rightarrow$ `CLIENT`, UNIQUE), `survey_id` (UUID, FK $\rightarrow$ `SURVEY`, NOT NULL), `assigned_category` (VARCHAR: `'CONSERVATIVE'`, `'MODERATE'`, `'AGGRESSIVE'`, `'UNDER_EVALUATION'`), `evaluation_status` (VARCHAR: `'COMPLETED'`, `'ERROR'`), `total_score` (NUMERIC, NULLABLE), `assigned_at` (TIMESTAMP).
   - *Restricciones:* Relación 0..1 por cliente (se actualiza mediante *upsert* en reevaluaciones). Si `evaluation_status = 'ERROR'`, entonces `assigned_category = 'UNDER_EVALUATION'` y `total_score IS NULL`.

### 5.2 Contrato de Interfaz Clave: `evaluateProfile`
- **Operación:** `CategorizationService.evaluate_profile(user_id: UUID, survey_id: UUID, answers: list[Answer]) -> EvaluationResult`
- **Precondiciones:** Invocada desde `SurveyManager.complete_survey` tras haber persistido la encuesta como `COMPLETED`. `answers` no está vacía y pertenece a `user_id`.
- **Postcondiciones (Éxito):** Calcula puntaje exacto en `ScoringEngine`, aplica `BR-03`, guarda en `FINANCIAL_PROFILE` con estado `'COMPLETED'` y retorna `EvaluationResult(survey_id, assigned_category, total_score, status="COMPLETED")`.
- **Manejo de Fallos (Escenario 3):** Si `answers` está vacía, lanza `InvalidInputError` sin tocar el perfil. Si ocurre cualquier excepción en cálculo o persistencia, registra log técnico seguro (sin PII ni respuestas), persiste perfil con `UNDER_EVALUATION` y estado `'ERROR'`, y retorna `EvaluationResult(survey_id, UNDER_EVALUATION, None, status="ERROR")`.

---

## 6. Hoja de Ruta y Checklist de Ejecución (`ADR-0002`)

### [x] Etapa Previa: Ingeniería de Requerimientos y Diseño (100% Completada)
- [x] Especificación de requerimiento Capstone `REQ-01` (User Story, Criterios Gherkin, Caso de Uso y Diagrama de Flujo).
- [x] `ADR-0001`: Selección del Stack Tecnológico.
- [x] `ADR-0002`: Estrategia Híbrida (*Walking Skeleton* + *Vertical Slices*).
- [x] `01_Architectural_and_Detailed_Design.md`: Diagrama de componentes, diagramas de clases UML (`Survey` y `Categorization`), responsabilidades y análisis de cohesión/acoplamiento.
- [x] `02_Interaction_and_Data_Design.md`: Diagramas de secuencia, modelo Entidad-Relación, tabla de *Data Ownership* y contrato formal de `evaluateProfile`.
- [x] `code_style.md` y `estructura_repositorio.md`.

---

### [x] Fase 0: Walking Skeleton (Completada en `feat/walking-skeleton-db` — 2026-11-12)
*Objetivo: Dejar operativa toda la tubería tecnológica E2E antes de codificar las reglas financieras. Criterio de salida: clonar repo, levantar contenedores/servicios, ver una petición viajando desde React hasta PostgreSQL y pasar `pytest` en verde.*

- [x] **1. Infraestructura y Base de Datos:**
  - [x] Crear `docker-compose.yml` en la raíz con PostgreSQL, volumen persistente y *healthcheck* (solo desarrollo local; la VM usa la BD provista por el profesor).
  - [x] Crear `.env.example` (sin IP ni credenciales reales) y `.gitignore` para Python, Node y entornos locales.
- [x] **2. Esqueleto de Backend (`backend/`):**
  - [x] Configurar `backend/pyproject.toml` (dependencias, `[build-system]`, Ruff, Mypy strict, Pytest).
  - [x] Implementar `src/core/config.py` (`CORS_ORIGINS`, `DEMO_MODE`), `src/core/database.py`, `src/core/schemas.py` (`CamelCaseSchema`), `src/core/auth_deps.py` (401 si el cliente no existe) y `src/core/models.py` (`ClientModel`, fuera de los módulos de dominio según *Data Ownership*).
  - [x] Configurar Alembic con la migración inicial de las 5 tablas (`8cedce29f65b`) y una segunda revisión con las restricciones del diseño 02 §2.2/§2.5 (`e4a1ef71cbd4`).
  - [x] Endpoint E2E `POST /api/v1/surveys/start` (`Router -> SurveyManager -> Repository -> PostgreSQL`) y `GET /api/v1/health` con verificación real de la BD.
  - [x] Script de datos demo idempotente (`scripts/seed_demo.py`) y prueba de humo por CLI (`scripts/smoke_test.sh`).
- [x] **3. Contrato OpenAPI y Esqueleto de Frontend (`frontend/`):**
  - [x] Inicializar aplicación React + Vite + TypeScript estricto en `frontend/` (pantalla en texto plano, sin estilos: solo verifica conectividad).
  - [x] Configurar script `openapi-typescript` (`npm run gen:api`) que exporta los esquemas de FastAPI a `frontend/src/api/generated/`.
  - [x] Conectar la pantalla base consumiendo el backend y `pytest` en verde (10 pruebas autocontenidas con rollback).
- [ ] **4. Cierre:** *merge* a `main` y despliegue en la VM siguiendo `README.md` §2.

**Pendientes conocidos que pasan a los Slices:** manejo de la carrera de `startSurvey` ante conflicto del índice único parcial (diseño 02 §2.4, Slice 3); autenticación real que reemplace `X-User-Id`/`DEMO_MODE`.

---

### [ ] Fase 1: Vertical Slice 1 — Camino Feliz (`REQ-01` Escenario 1 + `BR-01`, `BR-02`, `BR-03`)
- [ ] Semilla/carga de catálogo de hasta 10 preguntas parametrizadas (`QUESTION`) con pesos `Decimal`.
- [ ] Implementación de `ScoringEngine.calculate_score` y `ScoringEngine.determine_category` (aplicando `BR-03` en umbrales exactos).
- [ ] Implementación de `SurveyManager.start_survey` y `SurveyManager.complete_survey` transicionando a `COMPLETED` e invocando `CategorizationService.evaluate_profile`.
- [ ] Implementación de `ProfileRepository.save_category` (upsert sobre `FINANCIAL_PROFILE`).
- [ ] Construcción de vistas en React para responder cuestionario completo y visualizar pantalla de confirmación con categoría asignada y resumen derivado del plan.
- [ ] Pruebas unitarias de `ScoringEngine` (casos de borde `BR-03`) y prueba de integración E2E del flujo principal.

---

### [ ] Fase 2: Vertical Slice 2 — Resiliencia y Categoría Provisional (`REQ-01` Escenario 3)
- [ ] Implementación del bloque `try/except` en `CategorizationService.evaluate_profile` con logging seguro (sin PII, respuestas ni puntajes).
- [ ] Guardado de contingencia en `FINANCIAL_PROFILE` con `assigned_category = 'UNDER_EVALUATION'`, `evaluation_status = 'ERROR'` y `total_score = None`.
- [ ] Adaptación de la vista de resultados en React para mostrar aviso de falla temporal con categoría provisional "En Evaluación" y acceso habilitado al panel principal (sin pantalla de error 500).
- [ ] Pruebas automatizadas inyectando fallos simulados en motor/persistencia para verificar el retorno de `EvaluationResult` en estado `ERROR`.

---

### [ ] Fase 3: Vertical Slice 3 — Abandono y Reanudación de Borrador (`REQ-01` Escenario 2)
- [ ] Implementación de `SurveyManager.save_draft` garantizando que una encuesta `COMPLETED` rechace modificaciones (`SurveyAlreadyCompletedError`).
- [ ] Implementación de `SurveyRepository.find_draft_by_user_id` y `SurveyManager.resume_survey` (calculando la primera pregunta obligatoria sin respuesta en `ANSWER`).
- [ ] Integración en React para guardado parcial de respuestas y detección automática de borrador al reingresar, ubicando al usuario en la pregunta pendiente.
- [ ] Pruebas de integración verificando guardado de borrador, reanudación exacta e inmutabilidad de encuestas cerradas.

---

## 7. Preguntas Abiertas y Supuestos Registrados en Diseño

1. **Valores numéricos exactos de los umbrales de categoría:** `REQ-01` y `BR-03` especifican el comportamiento de desempate en el umbral, pero los valores exactos de corte entre `CONSERVATIVE`, `MODERATE` y `AGGRESSIVE` dependen de definición de producto/finanzas. En el código se parametrizarán en el constructor/configuración de `ScoringEngine` (ej. `conservative_threshold`, `moderate_threshold`).
2. **Catálogo de opciones por pregunta (`selected_option`):** Se modela como entero positivo con `option_value` (`Decimal`) resuelto.
3. **Fallo doble en persistencia provisional:** Si en el Escenario 3 también falla la escritura de `UNDER_EVALUATION` en la BD, no se introduce cola de mensajería (descartada por `ADR-0001`).
4. **Autenticación y Resumen del Plan:** El módulo de login/registro no hace parte del alcance de diseño detallado de `REQ-01` (se asume `user_id` provisto por dependencia de contexto), y el resumen del plan en el paso 6 es una vista derivada de la categoría asignada, no un módulo de persistencia independiente.