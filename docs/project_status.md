# Estado del Proyecto y Memoria de Contexto — Asesor Financiero Personal

| | |
| :--- | :--- |
| **Equipo** | Grupo 5 (`@KevinVerjan`, `@Estebandido-exe`, `@josuarezvi`, `@juacortesva`) |
| **Ubicación** | `PROJECT_STATUS.md` (Raíz del repositorio o `docs/PROJECT_STATUS.md`) |
| **Asignatura** | Ingeniería de Software I — Universidad Nacional de Colombia (UNAL) 2026-II |
| **Última Actualización** | 2026-11-11 |
| **Fase Actual** | Fase 0: *Walking Skeleton* (`ADR-0002`) |
| **Referencias** | `docs/code_style.md`, `docs/estructura_repositorio.md`, `docs/adr/adr-0001.md`, `docs/adr/adr_0002.md`, `docs/req/REQ-01.md`, `docs/design/01_Architectural_and_Detailed_Design.md`, `docs/design/02_Interaction_and_Data_Design.md` |

---

## 1. Resumen Ejecutivo y Propósito

El proyecto **Asesor Financiero Personal** es una aplicación web interactiva que permite registrar el perfil financiero de un cliente y evaluar su tolerancia al riesgo mediante un cuestionario breve de *onboarding* (`REQ-01`), asignando una categoría de inicio (`CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`) o un estado de contingencia (`UNDER_EVALUATION`) para personalizar su plan financiero.

Este documento actúa como **fuente de sincronización de estado (Single Source of Truth)** para desarrolladores y asistentes de IA. Todo código, script de infraestructura o documentación generada debe adherirse estrictamente a las restricciones y arquitectura aquí registradas.

---

## 2. Decisiones Arquitectónicas y Reglas Inmutables

| ID / Origen | Regla o Decisión | Restricción Técnica Obligatoria |
| :--- | :--- | :--- |
| **`ADR-0001`** | **Stack Tecnológico Políglota** | **Frontend:** React + Vite + TypeScript 5+.<br>**Backend:** Python 3.11+ + FastAPI + SQLAlchemy 2.0 + Pydantic v2.<br>**Base de Datos:** PostgreSQL 16+. |
| **`ADR-0001` / `code_style.md`** | **Precisión Numérica Estricta (Cero Floats)** | **Prohibido usar `float`** para puntajes, pesos de preguntas o valores financieros. En Python se usa exclusivamente `decimal.Decimal` inicializado desde `str` o `int`. En PostgreSQL se usa `NUMERIC(precision, scale)` con `asdecimal=True`. En JSON/TypeScript se serializa como `string`. |
| **`ADR-0002`** | **Estrategia de Construcción Híbrida** | **Prohibido desarrollar por capas horizontales aisladas.** Se ejecuta primero la **Fase 0 (*Walking Skeleton*)** de extremo a extremo y luego los **Cortes Verticales (*Vertical Slices* 1, 2 y 3)** alineados con los escenarios de `REQ-01`. |
| **`PROJECT_STRUCTURE`** | **Monorepo Modular por Dominio y Capas** | El código se divide primero por módulo de negocio (`survey/`, `categorization/`) y luego por capas internas con dependencia unidireccional estricta:<br>`router` $\longrightarrow$ `service` $\longrightarrow$ (`engine` \| `repository` $\longrightarrow$ `models`). |
| **`PROJECT_STRUCTURE`** | **Data Ownership Estricto** | Ningún módulo puede importar `models.py` ni `repository.py` de otro módulo. La comunicación entre módulos ocurre únicamente entre capas `service` intercambiando DTOs (`schemas.py`). |
| **`BR-01` (`REQ-01`)** | **Categoría Previa al Plan** | Todo cliente registrado debe tener un registro vigente en `FINANCIAL_PROFILE` antes de visualizar recomendaciones. |
| **`BR-02` (`REQ-01`)** | **Límite de Preguntas** | El cuestionario está limitado a un máximo de **10 preguntas activas** en la tabla `QUESTION` (tiempo estimado < 3 minutos). |
| **`BR-03` (`REQ-01`)** | **Desempate Conservador** | Si el puntaje calculado se ubica exactamente en el límite o umbral (`<=`) entre dos categorías financieras, `ScoringEngine` asigna por defecto la categoría de menor riesgo (más conservadora). |
| **`REQ-01` (Esc. 2)** | **Invariante de Borrador (`DRAFT`)** | Un cliente puede tener a lo sumo **un** borrador activo (`status = 'DRAFT'`). Una encuesta en estado `COMPLETED` es inmutable y rechaza cualquier invocación a `save_draft`. |
| **`REQ-01` (Esc. 3)** | **Tolerancia a Fallos Síncrona** | Si falla el cálculo o la persistencia en `evaluate_profile`, **no se lanza HTTP 500**. Se captura la excepción, se persiste `assigned_category = 'UNDER_EVALUATION'`, `evaluation_status = 'ERROR'` y `total_score = None`, devolviendo un `EvaluationResult` válido para permitir el ingreso al panel. Prohibido introducir brokers de mensajería (RabbitMQ/Celery). |
| **Seguridad / Logs** | **Privacidad de Datos Financieros** | **Prohibido registrar en logs** (`logger.error`, `print`) las respuestas del cliente (`answers`), puntajes (`total_score`) o PII. Solo se registra `error_type`, `operation` y marca de tiempo. El `user_id` siempre se extrae del contexto de autenticación en el `router`, nunca del body HTTP. |

---

## 3. Convenciones de Código y Límites Cuantitativos (`docs/code_style.md`)

### 3.1 Matriz de Nombres (Naming Case)

| Elemento | Python (Backend) | TypeScript / React (Frontend) | PostgreSQL (BD) | JSON (API REST) |
| :--- | :--- | :--- | :--- | :--- |
| **Variables, funciones y métodos** | `snake_case` (`evaluate_profile`, `user_id`) | `camelCase` (`evaluateProfile`, `userId`) | N/A | `camelCase` (`surveyId`, `totalScore`) |
| **Clases, Modelos, Componentes UI** | `PascalCase` (`SurveyManager`, `ScoringEngine`) | `PascalCase` (`SurveyForm`, `EvaluationCard`) | N/A | N/A |
| **Schemas / Interfaces / DTOs** | `PascalCase` heredando de `CamelCaseSchema` | `PascalCase` (`EvaluationResult`) | N/A | Conversión automática `to_camel` |
| **Constantes y Enums** | `UPPER_SNAKE_CASE` (`UNDER_EVALUATION`) | `UPPER_SNAKE_CASE` (`UNDER_EVALUATION`) | `'DRAFT'`, `'COMPLETED'` | `'UNDER_EVALUATION'` |
| **Tablas y Columnas SQL** | Atributos en `snake_case` (`client_id`) | N/A | `snake_case` (`financial_profile`) | N/A |
| **Archivos y Módulos** | `snake_case.py` (`scoring_engine.py`) | Componentes: `PascalCase.tsx`<br>Hooks/Utils: `camelCase.ts` | Migraciones: `snake_case.sql` | N/A |

### 3.2 Reglas de Calidad y Pruebas
- **Límites estáticos:** Máximo **88 caracteres** por línea en Python (`Ruff`) y **100 caracteres** en TypeScript (`ESLint + Prettier`).
- **Tamaño de funciones:** Máximo **35 líneas efectivas** (sin docstring), máximo **4 parámetros** por firma (usar DTO si requiere más), máximo **3 niveles de indentación** (obligatorio usar *Early Return* / cláusulas de guarda) y complejidad ciclomática **$\le 10$** (`Ruff C901`).
- **Tipado:** `mypy --strict` en Python (cero funciones sin Type Hints) y `strict: true` en TypeScript (prohibido usar `any`).
- **Nomenclatura de Tests (`pytest` / `Vitest`):** Patrón `test_<operacion>_when_<condicion>_then_<resultado_esperado>` estructurado con bloques separados **AAA (Arrange - Act - Assert)**.

---

## 4. Arquitectura de Datos y Contratos de Dominio (`docs/design/`)

### 4.1 Esquema Relacional (PostgreSQL)

1. **`client`**: `client_id` (UUID, PK), `email` (VARCHAR, UNIQUE, NOT NULL), `created_at` (TIMESTAMP).
2. **`survey`**: `survey_id` (UUID, PK), `client_id` (UUID, FK $\rightarrow$ `client`), `status` (VARCHAR: `'DRAFT'` | `'COMPLETED'`), `started_at`, `completed_at` (NULLABLE), `updated_at`.
   - *Constraint:* Índice único parcial sobre `(client_id) WHERE status = 'DRAFT'`.
3. **`question`**: `question_id` (INT, PK), `text` (VARCHAR, NOT NULL), `weight` (NUMERIC, NOT NULL, $\ge 0$), `display_order` (INT, UNIQUE), `is_required` (BOOLEAN).
   - *Constraint:* Máximo 10 preguntas activas (`BR-02`).
4. **`answer`**: `answer_id` (UUID, PK), `survey_id` (UUID, FK $\rightarrow$ `survey`), `question_id` (INT, FK $\rightarrow$ `question`), `selected_option` (INT, $> 0$), `option_value` (NUMERIC, NOT NULL).
   - *Constraint:* Unique `(survey_id, question_id)`.
5. **`financial_profile`**: `profile_id` (UUID, PK), `client_id` (UUID, FK UNIQUE $\rightarrow$ `client`), `survey_id` (UUID, FK $\rightarrow$ `survey`), `assigned_category` (`'CONSERVATIVE'` | `'MODERATE'` | `'AGGRESSIVE'` | `'UNDER_EVALUATION'`), `evaluation_status` (`'COMPLETED'` | `'ERROR'`), `total_score` (NUMERIC, NULLABLE), `assigned_at` (TIMESTAMP).

### 4.2 Equivalencia de Operaciones UML $\leftrightarrow$ Python

| Componente / Clase | Operación en Diseño (UML) | Firma Exacta en Python (`snake_case`) |
| :--- | :--- | :--- |
| **`SurveyManager`** (`survey/service.py`) | `startSurvey(userId)` | `start_survey(self, user_id: UUID) -> Survey` |
| **`SurveyManager`** (`survey/service.py`) | `saveDraft(surveyId, userId, answers)` | `save_draft(self, survey_id: UUID, user_id: UUID, answers: list[Answer]) -> None` |
| **`SurveyManager`** (`survey/service.py`) | `resumeSurvey(userId)` | `resume_survey(self, user_id: UUID) -> Survey | None` |
| **`SurveyManager`** (`survey/service.py`) | `completeSurvey(surveyId, userId)` | `complete_survey(self, survey_id: UUID, user_id: UUID) -> EvaluationResult` |
| **`SurveyRepository`** (`survey/repository.py`) | `findById(surveyId, userId)` | `find_by_id(self, survey_id: UUID, user_id: UUID) -> Survey | None` |
| **`SurveyRepository`** (`survey/repository.py`) | `findDraftByUserId(userId)` | `find_draft_by_user_id(self, user_id: UUID) -> Survey | None` |
| **`CategorizationService`** (`categorization/service.py`) | `evaluateProfile(userId, surveyId, answers)` | `evaluate_profile(self, user_id: UUID, survey_id: UUID, answers: list[Answer]) -> EvaluationResult` |
| **`ScoringEngine`** (`categorization/engine.py`) | `calculateScore(answers)` | `calculate_score(self, answers: list[Answer]) -> Decimal` |
| **`ScoringEngine`** (`categorization/engine.py`) | `determineCategory(score)` | `determine_category(self, score: Decimal) -> FinancialCategory` |
| **`ProfileRepository`** (`categorization/repository.py`) | `saveCategory(userId, surveyId, category, status)` | `save_category(self, user_id: UUID, survey_id: UUID, category: FinancialCategory, status: EvaluationStatus, total_score: Decimal | None = None) -> None` |

---

## 5. Estado del Repositorio (Realidad Actual vs. Estructura Objetivo)

### 5.1 Archivos Existentes Hoy en `main`
```text
Grupo-5-Finanzas-Ingesoft_I_UN_2026-II/
├── README.md
├── PROJECT_STATUS.md                                  # Este documento de contexto
└── docs/
    ├── code_style.md                                  # Estándares Ruff, ESLint, Decimal, Logs
    ├── estructura_repositorio.md                      # Reglas de monorepo y capas
    ├── adr/
    │   ├── adr-0001.md                                # Stack React + FastAPI + PostgreSQL
    │   └── adr_0002.md                                # Walking Skeleton + Vertical Slices
    ├── design/
    │   ├── 01_Architectural_and_Detailed_Design.md    # Diagramas de componentes y clases
    │   └── 02_Interaction_and_Data_Design.md         # Diagramas de secuencia, ER y contratos
    ├── req/
    │   ├── REQ-01.md                                  # Requerimiento Capstone validado
    │   └── REQ-02.md                                  # Plantilla vacía sin especificar
    └── rfc/
        └── rfc_proyecto.md                            # Borrador inicial RFC
```

### 5.2 Árbol Objetivo a Construir (`docs/estructura_repositorio.md`)
```text
Grupo-5-Finanzas-Ingesoft_I_UN_2026-II/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── src/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── exceptions.py
│   │   │   ├── security.py
│   │   │   └── schemas.py
│   │   ├── survey/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   └── enums.py
│   │   └── categorization/
│   │       ├── router.py
│   │       ├── service.py
│   │       ├── engine.py
│   │       ├── repository.py
│   │       ├── models.py
│   │       ├── schemas.py
│   │       └── enums.py
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       └── integration/
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    └── src/
        ├── api/
        │   └── generated/
        ├── features/
        │   ├── survey/
        │   │   ├── components/
        │   │   ├── hooks/
        │   │   ├── pages/
        │   │   └── types.ts
        │   └── categorization/
        │       ├── components/
        │       ├── hooks/
        │       ├── pages/
        │       └── types.ts
        └── shared/
            ├── components/
            └── utils/
```

---

## 6. Roadmap y Checklist de Ejecución (`ADR-0002`)

### Fase Previa: Ingeniería de Requerimientos y Diseño
- [x] Especificación de `REQ-01` (User Story, Criterios Gherkin AC-01.1 a 01.3, Caso de Uso).
- [x] Registro de `ADR-0001` (Stack) y `ADR-0002` (Estrategia de construcción).
- [x] Diseño Arquitectónico y Detallado (`01_Architectural_and_Detailed_Design.md`).
- [x] Diseño de Interacción, Modelo ER y Contratos (`02_Interaction_and_Data_Design.md`).
- [x] Definición de Guía de Estilo (`code_style.md`) y Estructura (`estructura_repositorio.md`).

### Fase 0: Walking Skeleton (EN CURSO — Prioridad Inmediata)
*Meta: Clonar el repo, levantar contenedores/servicios, ejecutar `pytest` en verde y completar una petición real desde React hasta PostgreSQL.*

- [ ] **1. Infraestructura y Base de Datos:**
  - [ ] Crear `docker-compose.yml` con servicio PostgreSQL, volumen persistente y `healthcheck`.
  - [ ] Crear `.env.example` y `.gitignore` raíz para Python, Node y entornos locales.
- [ ] **2. Esqueleto Backend (`backend/`):**
  - [ ] Configurar `backend/pyproject.toml` con dependencias (`fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pydantic-settings`) y herramientas (`ruff`, `mypy`, `pytest`).
  - [ ] Implementar `src/core/config.py`, `src/core/database.py` y `src/core/schemas.py` (`CamelCaseSchema`).
  - [ ] Configurar Alembic (`alembic/env.py`) y generar la migración inicial con las 5 tablas del modelo ER (`client`, `survey`, `question`, `answer`, `financial_profile`).
  - [ ] Crear estructura de paquetes vacíos en `src/survey/` y `src/categorization/` junto con dependencia mock/base de autenticación (`get_current_user_id`) en `src/core/security.py`.
  - [ ] Exponer endpoint de conectividad en `src/main.py` con CORS habilitado y verificar `/docs` (Swagger UI).
- [ ] **3. Esqueleto Frontend y Contratos (`frontend/`):**
  - [ ] Inicializar aplicación React + Vite + TypeScript en `frontend/`.
  - [ ] Configurar `openapi-typescript` en `package.json` y exportar los esquemas de FastAPI hacia `frontend/src/api/generated/`.
  - [ ] Conectar pantalla base en React que consuma el backend de extremo a extremo.
- [ ] **4. Pipeline de Pruebas Inicial:**
  - [ ] Configurar `backend/tests/conftest.py` y ejecutar primera prueba automatizada en `pytest` en verde.

### Fase 1: Vertical Slice 1 — Camino Feliz (`REQ-01` Escenario 1 + `BR-01`, `BR-02`, `BR-03`)
- [ ] Seed/migración de datos con el catálogo de hasta 10 preguntas parametrizadas (`BR-02`).
- [ ] Implementar `SurveyManager.start_survey` y `SurveyManager.complete_survey` transicionando a `COMPLETED`.
- [ ] Implementar `ScoringEngine.calculate_score` (aritmética `Decimal`) y `ScoringEngine.determine_category` (aplicando desempate conservador `BR-03`).
- [ ] Implementar `CategorizationService.evaluate_profile` y `ProfileRepository.save_category` guardando estado `COMPLETED` (`BR-01`).
- [ ] Construir UI de cuestionario en `frontend/src/features/survey/` y vista de confirmación con categoría asignada en `categorization/`.
- [ ] Pruebas unitarias de `ScoringEngine` (incluyendo casos de borde exactos en umbrales para `BR-03`) y prueba de integración del flujo completo.

### Fase 2: Vertical Slice 2 — Resiliencia y Categoría Provisional (`REQ-01` Escenario 3)
- [ ] Implementar bloque `try/except` en `CategorizationService.evaluate_profile`.
- [ ] Asegurar logging sanitario (sin respuestas, puntajes ni PII) y persistencia de contingencia con `assigned_category = FinancialCategory.UNDER_EVALUATION`, `evaluation_status = EvaluationStatus.ERROR` y `total_score = None`.
- [ ] Adaptar UI en `frontend/` para mostrar aviso de falla temporal con categoría provisional `"En Evaluación"` permitiendo acceso al panel principal sin pantalla de error 500.
- [ ] Pruebas unitarias y de integración inyectando fallos en cálculo/persistencia para comprobar el retorno seguro del contrato.

### Fase 3: Vertical Slice 3 — Abandono y Reanudación de Borrador (`REQ-01` Escenario 2)
- [ ] Implementar `SurveyManager.save_draft` garantizando el invariante de a lo sumo un `DRAFT` activo por `client_id` y rechazando cambios sobre encuestas `COMPLETED` (`SurveyAlreadyCompletedError`).
- [ ] Implementar `SurveyRepository.find_draft_by_user_id` y `SurveyManager.resume_survey` derivando la primera pregunta obligatoria pendiente.
- [ ] Implementar guardado parcial en React y detección automática de borrador al reingresar.
- [ ] Pruebas de integración verificando guardado parcial, recuperación exacta de respuestas y rechazo de modificación en encuestas cerradas.

---

## 7. Preguntas Abiertas y Supuestos Activos (`02_Interaction_and_Data_Design.md`)

1. **Umbrales numéricos exactos de cada banda:** `REQ-01` y `BR-03` especifican la regla de desempate en el umbral, pero no los números exactos de corte entre `CONSERVATIVE`, `MODERATE` y `AGGRESSIVE`. *Mitigación:* Parametrizar los límites (`conservative_threshold`, `moderate_threshold`) en el constructor/configuración de `ScoringEngine`.
2. **Catálogo de opciones por pregunta (`selected_option`):** Se modela como entero positivo con `option_value: Decimal` resuelto.
3. **Fallo doble en persistencia de contingencia:** Si falla el `try` principal y también falla el `save_category` provisional del `except`, `evaluate_profile` retorna igualmente el DTO `EvaluationResult` con `UNDER_EVALUATION` y `status = ERROR` para no bloquear al cliente con un HTTP 500.
4. **Autenticación y Resumen del Plan:** El módulo de login no hace parte del alcance de diseño detallado de `REQ-01` (se asume `user_id` inyectado por dependencia de FastAPI), y el resumen del plan es una vista derivada de la categoría asignada en el frontend.