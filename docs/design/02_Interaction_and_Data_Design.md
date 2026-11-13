# Asesor Financiero Personal — Interaction & Data Design v1.2

| | |
|---|---|
| **Team** | Grupo 5 |
| **Members** | Esteban David Suárez<br />Juan David Cortés<br />Joel Felipe Suárez<br />Kevin Facid Verjan |
| **Status** | Definitive design baseline — open decisions documented in §5 |
| **Date** | 2026-10-25 (aligned 2026-11-12) |
| **Inputs** | `docs/design/01_Architectural_and_Detailed_Design.md` (v1.1), `docs/req/REQ-01.md`, `docs/adr/adr-0001.md`, Interaction & Contracts Design v0.1 (Class 13) |

---

## 1. Behavior — Selected Use Cases

Se modelan **tres interacciones** derivadas del único caso de uso escrito en `REQ-01`; no son tres casos de uso independientes. La primera es el **happy-path** completo (captura + evaluación). La segunda es el **flujo alternativo de abandono y reanudación** (Escenario 2). La tercera es la **respuesta al riesgo de `REQ-01`**: violación de ownership. No se inventa un segundo requerimiento.

**Nota transversal — origen del `userId`.** En todos los diagramas, el `userId` (`user_id` en Python) se obtiene del contexto de autenticación validado por el backend (dependencia de FastAPI `Depends(get_current_user)` / `getCurrentUser()` en UML), **nunca** del cuerpo de la petición HTTP. El participante `Auth Dependency` representa esa dependencia, no un módulo de autenticación diseñado en la Entrega 1. La dependencia se ejecuta en el servidor al procesar cada petición; la `Web App` no la invoca directamente. En persistencia, `userId`/`user_id` corresponde a `client.client_id`.

### 1.1 Happy-Path: Catalogar Situación Financiera y Asignar Categoría — REQ-01 (Escenario 1)

**Precondición:** el cliente creó una cuenta y está autenticado. **Supuesto de diseño:** la dependencia de autenticación entrega el `userId` al `SurveyRouter` antes de que este delegue en `SurveyManager`. El módulo de autenticación no está diseñado en la Entrega 1 y no se introduce como componente nuevo.

```mermaid
sequenceDiagram
    actor Cliente
    participant WebApp as Web App
    participant Auth as Auth Dependency<br/>(FastAPI Depends)
    participant SRouter as SurveyRouter
    participant SMgr as SurveyManager
    participant SRepo as SurveyRepository
    participant CSvc as CategorizationService
    participant SEng as ScoringEngine
    participant PRepo as ProfileRepository

    Cliente->>WebApp: inicia onboarding
    WebApp->>SRouter: startSurvey() [HTTP]
    SRouter->>Auth: getCurrentUser() [FastAPI Depends]
    Auth-->>SRouter: userId validado
    SRouter->>SMgr: startSurvey(userId)
    SMgr->>SRepo: findDraftByUserId(userId)
    SRepo-->>SMgr: draft or null
    alt no existe DRAFT
        SMgr->>SRepo: save(new Survey en DRAFT)
        SRepo-->>SMgr: persisted DRAFT
    else ya existe DRAFT
        Note right of SMgr: idempotente: devuelve el existente
    end
    SMgr-->>SRouter: Survey DRAFT + catálogo de preguntas
    SRouter-->>WebApp: surveyId + questions
    WebApp-->>Cliente: presenta cuestionario

    loop por cada pregunta respondida
        Cliente->>WebApp: responde pregunta
        WebApp->>SRouter: saveAnswer(surveyId, answer) [HTTP]
        SRouter->>Auth: getCurrentUser() [FastAPI Depends]
        Auth-->>SRouter: userId validado
        SRouter->>SMgr: saveAnswer(surveyId, userId, answer)
        SMgr->>SRepo: findById(surveyId, userId)
        SRepo-->>SMgr: Survey (DRAFT o COMPLETED) o null
        alt survey existe y pertenece al userId
            SMgr->>SMgr: validar status = DRAFT
            alt status = DRAFT
                SMgr->>SRepo: saveAnswer(surveyId, userId, answer)
                SRepo-->>SMgr: persisted
                SMgr-->>SRouter: ok
                SRouter-->>WebApp: ok
                WebApp-->>Cliente: confirmación visual
            else status = COMPLETED
                SMgr-->>SRouter: InvalidStateError
                SRouter-->>WebApp: 409 Conflict
                WebApp-->>Cliente: encuesta ya cerrada
            end
        else survey no encontrada o no pertenece al usuario
            SMgr-->>SRouter: NotFoundError
            SRouter-->>WebApp: 404 Not Found
            WebApp-->>Cliente: recurso no encontrado
        end
    end

    Cliente->>WebApp: confirma envío
    WebApp->>SRouter: completeSurvey(surveyId) [HTTP]
    SRouter->>Auth: getCurrentUser() [FastAPI Depends]
    Auth-->>SRouter: userId validado
    SRouter->>SMgr: completeSurvey(surveyId, userId)
    SMgr->>SRepo: findById(surveyId, userId)
    SRepo-->>SMgr: Survey DRAFT con answers
    alt survey válida, DRAFT, respuestas completas
        SMgr->>SRepo: save(survey COMPLETED) [transacción]
        Note right of SRepo: commit de COMPLETED antes de evaluar
        SMgr->>CSvc: evaluateProfile(userId, surveyId, scoredAnswers)
        CSvc->>SEng: calculateScore(scoredAnswers)
        SEng-->>CSvc: totalScore
        CSvc->>SEng: determineCategory(totalScore)
        SEng-->>CSvc: assignedCategory
        alt cálculo y persistencia exitosos
            CSvc->>PRepo: saveCategory(userId, ProfileEvaluation(surveyId, category, COMPLETED, totalScore))
            PRepo-->>CSvc: persisted FinancialProfile
            CSvc-->>SMgr: EvaluationResult COMPLETED
        else fallo del motor o de la persistencia de la categoría definitiva
            CSvc->>CSvc: logError(errorType, operation, timestamp)
            CSvc->>PRepo: saveCategory(userId, ProfileEvaluation(surveyId, UNDER_EVALUATION, ERROR, null))
            alt persistencia provisional exitosa
                PRepo-->>CSvc: persisted provisional
                CSvc-->>SMgr: EvaluationResult ERROR
            else también falla la persistencia provisional
                PRepo-->>CSvc: persistence failure
                CSvc-->>SMgr: EvaluationPersistenceError
                Note over CSvc,PRepo: No se garantiza que exista o se actualice financial_profile
            end
        end
        alt evaluación completada o perfil provisional persistido
            SMgr-->>SRouter: EvaluationResult
            SRouter-->>WebApp: categoría + evaluationStatus
            WebApp-->>Cliente: confirmación y resumen del plan
        else también falla la persistencia provisional
            SMgr-->>SRouter: EvaluationPersistenceError
            SRouter-->>WebApp: error de evaluación no recuperable en esta operación
            WebApp-->>Cliente: informar que no se pudo completar la evaluación
        end
    else survey inválida (no existe, no es del usuario, ya COMPLETED o incompleta)
        SMgr-->>SRouter: NotFoundError / InvalidStateError / ValidationError
        SRouter-->>WebApp: 404 / 409 / 422
        WebApp-->>Cliente: envío rechazado
    end
```

| Use Case step or flow | Message(s) in the diagram | Information exchanged | Operation defined in (Deliverable 1) |
|---|---|---|---|
| Precondición: cliente autenticado | `getCurrentUser()`, `userId` | token/sesión → `userId` | Dependencia de FastAPI (`get_current_user`), no diseñada en Entrega 1 |
| Main flow, paso 1–2: inicio de la encuesta | `startSurvey`, `findDraftByUserId`, `save` | `userId`, `Survey DRAFT` (nuevo o existente) | `SurveyManager.startSurvey`, `SurveyRepository.findDraftByUserId`, `SurveyRepository.save` |
| Main flow, paso 2: carga del catálogo | `questions` en el output de `startSurvey` | catálogo de `question` (`BR-01`) | `SurveyManager.startSurvey` (output `Survey` incluye `questions`) |
| Main flow, paso 3 (progresivo): captura de cada respuesta | `saveAnswer`, `findById`, `saveAnswer` | `surveyId`, `userId`, `answer` individual; `SurveyManager` valida estado `DRAFT` y reglas antes de persistir | `SurveyManager.saveAnswer`, `SurveyRepository.findById`, `SurveyRepository.saveAnswer` |
| Main flow, paso 4–5: envío y evaluación (incluye `BR-03`, `BR-05`) | `completeSurvey`, `evaluateProfile`, `calculateScore`, `determineCategory` | `userId`, `surveyId`, `scoredAnswers` (`ScoredAnswerDTO`), `totalScore`, categoría | `SurveyManager.completeSurvey`, `CategorizationService.evaluateProfile`, `ScoringEngine.calculateScore`, `ScoringEngine.determineCategory` |
| Main flow, paso 6: persistencia exitosa (`BR-04`) | `saveCategory(userId, ProfileEvaluation(...))` con `COMPLETED` | categoría, `totalScore`, `evaluationStatus = COMPLETED` | `ProfileRepository.saveCategory` |
| Exception flow (Escenario 3 `REQ-01`, `BR-06`): fallo del motor | `logError`, `saveCategory(userId, ProfileEvaluation(...))` con `UNDER_EVALUATION`/`ERROR` | `errorType`, `operation`, `timestamp` (sin datos sensibles); perfil provisional si su persistencia tiene éxito | `CategorizationService.evaluateProfile` (bloque de excepción de §3.4 del `01`) |
| Alternative rechazada: envío inválido o estado no `DRAFT` | `else survey inválida` | `NotFoundError`, `InvalidStateError`, `ValidationError` | `completeSurvey` / precondiciones de `evaluateProfile` |

*Cada mensaje tiene un propósito (autenticar, cargar, transicionar, calcular, persistir o notificar). El orden respeta las capas del `01` (`Router → Service → Repository` y `survey` → `categorization`). `BR-05` queda encapsulado en `determineCategory`. El resumen visual del paso 7 en `REQ-01` es presentación derivada de la categoría. La persistencia de respuestas es **progresiva**: cada `saveAnswer` es una transacción independiente, lo que responde al requisito de recuperación tras desconexión (ver §1.2).*

### 1.2 Abandono, Recuperación y Reanudación — REQ-01 (Escenario 2)

**Supuesto de diseño:** el abandono no se modela como una operación explícita del cliente (`saveDraft` en `beforeunload` no es confiable). Cada respuesta ya está persistida por `saveAnswer` cuando el cliente interrumpe el flujo. La "recuperación" es una lectura: `resumeSurvey(userId)` trae el `DRAFT` existente (`BR-02`) con todas las respuestas persistidas hasta el último `saveAnswer` exitoso.

```mermaid
sequenceDiagram
    actor Cliente
    participant WebApp as Web App
    participant Auth as Auth Dependency
    participant SRouter as SurveyRouter
    participant SMgr as SurveyManager
    participant SRepo as SurveyRepository

    Note over Cliente,SRepo: Fase de abandono (implícita)
    Note right of Cliente: El cliente cierra el navegador,<br/>pierde conexión o cierra sesión.<br/>No hay operación explícita:<br/>las respuestas ya están persistidas<br/>por saveAnswer previos.

    Note over Cliente,SRepo: Fase de reingreso
    Cliente->>WebApp: reingresa a la aplicación
    WebApp->>SRouter: resumeSurvey() [HTTP]
    SRouter->>Auth: getCurrentUser() [FastAPI Depends]
    Auth-->>SRouter: userId validado
    SRouter->>SMgr: resumeSurvey(userId)
    SMgr->>SRepo: findDraftByUserId(userId)
    alt existe DRAFT para el cliente
        SRepo-->>SMgr: Survey DRAFT + answers + questions
        SMgr-->>SRouter: Survey con respuestas persistidas
        SRouter-->>WebApp: surveyId, answers[], questions[]
        Note over WebApp: nextQuestion = primera question<br/>obligatoria sin answer asociado
        WebApp-->>Cliente: presenta el cuestionario en nextQuestion
    else no existe DRAFT
        SRepo-->>SMgr: null
        SMgr-->>SRouter: no draft
        SRouter-->>WebApp: empty
        WebApp->>SRouter: startSurvey()
        Note over SRouter: ver §1.1 para la creación del DRAFT
        WebApp-->>Cliente: presenta el cuestionario desde el inicio
    end
```

| Use Case step or flow | Message(s) in the diagram | Information exchanged | Operation defined in (Deliverable 1) |
|---|---|---|---|
| Alternative flow: abandono con respuestas parciales | (implícito, no hay mensaje) | estado persistido en `answer` por `saveAnswer` previos | `SurveyRepository.saveAnswer` (invocado durante la captura) |
| Alternative flow: reingreso y reanudación | `resumeSurvey`, `findDraftByUserId` | `userId`, encuesta `DRAFT` con sus `answer` | `SurveyManager.resumeSurvey`, `SurveyRepository.findDraftByUserId` |
| Alternative of resume: no hay borrador | `else no existe DRAFT` | ausencia de encuesta abierta; se dispara `startSurvey` | `resumeSurvey`, `startSurvey` |
| Derivación del cursor de UI | `nextQuestion` calculado en el cliente | comparación entre `question` obligatorias y `answer` existentes | No persistido; derivado en presentación (ver §2.1) |

*La "última pregunta pendiente" **no** se persiste como cursor de UI: se recomputa como la primera `question` obligatoria sin `answer` asociada, comparando el catálogo vigente con las respuestas recuperadas. Persistir el cursor se desincronizaría si cambia el orden del catálogo (ver §2.1). El abandono no requiere una operación `saveDraft` batch: la persistencia progresiva de §1.1 ya deja las respuestas en PostgreSQL, que es la **única fuente autoritativa**.*

### 1.3 Violación de Ownership — Respuesta al riesgo de REQ-01

Este flujo materializa el riesgo de filtración de datos formulado en `docs/req/REQ-01.md`. Es la evidencia visual de la mitigación: **el backend no distingue entre "no existe" y "existe pero no es tuyo"**, por lo que responde 404 en ambos casos (no 403, no 500), evitando filtrar la existencia del recurso.

```mermaid
sequenceDiagram
    actor ClienteA as Cliente A (autenticado)
    participant WebApp as Web App
    participant Auth as Auth Dependency
    participant SRouter as SurveyRouter
    participant SMgr as SurveyManager
    participant SRepo as SurveyRepository

    ClienteA->>WebApp: solicita operación sobre surveyId
    WebApp->>SRouter: op(surveyId) [HTTP]
    SRouter->>Auth: getCurrentUser() [FastAPI Depends]
    Auth-->>SRouter: userIdA validado
    SRouter->>SMgr: op(surveyId, userIdA, ...)
    SMgr->>SRepo: findById(surveyId, userIdA)
    Note right of SRepo: WHERE survey_id = :surveyId<br/>AND client_id = :userIdA
    alt encuesta no existe o no pertenece a userIdA
        SRepo-->>SMgr: null
        SMgr-->>SRouter: NotFoundError
        SRouter-->>WebApp: 404 Not Found
        WebApp-->>ClienteA: "recurso no encontrado"
    else encuesta pertenece a userIdA
        SRepo-->>SMgr: Survey
        alt operación es lectura (resumeSurvey, findById) o el survey está en DRAFT
            SMgr-->>SRouter: resultado
            SRouter-->>WebApp: resultado
            WebApp-->>ClienteA: información de la encuesta
        else operación es saveAnswer y el survey está COMPLETED
            SMgr-->>SRouter: InvalidStateError
            SRouter-->>WebApp: 409 Conflict
            WebApp-->>ClienteA: "la encuesta ya está cerrada"
        end
    end
```

| Use Case step or flow | Message(s) in the diagram | Information exchanged | Operation defined in (Deliverable 1) |
|---|---|---|---|
| Riesgo de `REQ-01`: acceso o modificación no autorizados | `getCurrentUser`, `findById(surveyId, userIdA)` | `userIdA` (autenticado); `surveyId` (posiblemente ajeno) | `SurveyRepository.findById` (filtro por `client_id = userIdA` en la query) |
| Caso violación: `surveyId` es de otro usuario | rama `null` del `alt` | rechazo sin revelar existencia | `SurveyRepository.findById` + traducción a 404 en `SurveyManager` / `SurveyRouter` |
| Caso violación: intento de modificar `COMPLETED` (`BR-03`) | rama `InvalidStateError` | rechazo de mutación; `COMPLETED` es inmutable | Validación de estado `DRAFT` en `SurveyManager.saveAnswer` antes de persistir en `SurveyRepository` (ley de capas de `docs/estructura_repositorio.md`) |
| Caso legítimo: lectura o `DRAFT` propio | rama `Survey` del `alt` | resultado normal | `findById`, `resumeSurvey` |

*Decisión de diseño explícita: **404, no 403**. Un 403 le confirmaría al atacante que la encuesta existe pero pertenece a otro usuario, filtrando información. Un 404 es indistinguible de "no existe". Esta misma lógica aplica a `ProfileRepository.findByUserId`: solo devuelve el perfil del `userId` autenticado. La comprobación respeta las capas: `SurveyRepository` filtra en la query (`WHERE client_id = :userId`) y `SurveyManager` valida las reglas de negocio y el estado (`status = DRAFT` para `saveAnswer`).*

---

## 2. Data Design

### 2.1 Principal information the system needs

| Information | Needed by (use cases) | Persisted? | Why (or why not) |
|---|---|---|---|
| Identidad del cliente (`userId` / `user_id`) | Todos los flujos | **No** en el modelo de encuestas; vive en el token/sesión | El `userId` (`user_id` en Python) se obtiene del contexto de autenticación y corresponde al valor de `client.client_id`. `survey.client_id` y `financial_profile.client_id` lo referencian como FK. No se persisten credenciales ni datos de sesión en el modelo de encuestas. |
| Encuesta y su estado (`DRAFT` / `COMPLETED`) | Happy-path, reanudación, violación de ownership | Yes | El Escenario 2 (`BR-02`) exige recuperar un borrador. El flujo principal (`BR-03`) exige transicionar a `COMPLETED`. **`survey.status` no incluye `ERROR`:** ese estado pertenece a `financial_profile.evaluation_status`. |
| Respuestas del cliente | Happy-path (cálculo), reanudación (progreso) | Yes | Sin persistirlas, el abandono perdería información. Son la única entrada del motor de evaluación. Se persisten **progresivamente** por `saveAnswer`, no en lote. |
| Catálogo de preguntas (texto, peso, orden, obligatoriedad) | Happy-path, reanudación | Yes | El caso de uso habla de preguntas parametrizadas y `BR-01` limita a 10. Deben existir con identidad estable para referenciar respuestas. |
| Perfil financiero (categoría, estado de evaluación, puntaje, encuesta origen) | Happy-path | Yes | `BR-04`: todo cliente que completa la encuesta obtiene exactamente una categoría vigente. El Escenario 3 (`BR-06`) exige persistir `UNDER_EVALUATION` con `evaluation_status = ERROR`. |
| Matriz de umbrales / algoritmo de desempate `BR-05` | Happy-path | **No** | Conocimiento encapsulado en `ScoringEngine` (ocultamiento de información). Persistirlo como tabla crearía una segunda fuente de verdad. |
| ETA / datos bancarios / extractos | Ninguno en `REQ-01` | **No** | Restricción explícita: la categorización se resuelve internamente sin APIs bancarias. |
| Resumen visual del plan | Happy-path, paso 6 | **No** | No existe módulo de Plan. Se deriva de la categoría asignada en presentación. |
| Cursor de UI (índice de última pantalla) | Reanudación | **No** | Se recomputa como la primera `question` obligatoria sin `answer`. Un cursor persistido se desincronizaría si cambia el orden del catálogo. |

### 2.2 Data model

**Justificación de representación (formato pedido):** Because [`ADR-0001`](../adr/adr-0001.md) exige PostgreSQL con integridad referencial y `NUMERIC` para puntajes / We chose [modelo relacional Entidad-Relación, no documentos] / Accepting [un esquema más rígido y migraciones ante cambios de catálogo, a cambio de no duplicar fuentes de verdad entre encuesta y perfil].

Otras decisiones del modelo, con el mismo formato:

| Decision | Because / We chose / Accepting |
|---|---|
| Perfil financiero separado de la encuesta | Because [`BR-04` coloca la categoría vigente en el cliente vinculada a la encuesta origen] / We chose [un `financial_profile` 0..1 por cliente, separado del historial de encuestas en `survey`] / Accepting [`survey_id` en el perfil referencia la encuesta origen de la categoría vigente, no un historial completo de evaluaciones] |
| Preguntas como catálogo compartido, no snapshot por encuesta | Because [el cuestionario es parametrizado y acotado por `BR-01`] / We chose [tabla `question` referenciada por `answer`] / Accepting [editar el texto o el peso de una pregunta puede reinterpretar encuestas antiguas si no hay versionado — ver §5] |
| A lo sumo un `DRAFT` por cliente | Because [`BR-02` y el Escenario 2 exigen a lo sumo una encuesta en borrador activa por cliente] / We chose [invariante de unicidad parcial sobre `(client_id)` donde `status = 'DRAFT'`] / Accepting [el cliente no puede iniciar un segundo cuestionario hasta completar o descartar el borrador — el descarte no está especificado] |
| Puntaje nulo cuando el estado de evaluación es `ERROR` | Because [`BR-06` y la sección 3.4 del `01` devuelven `totalScore = null` en el Escenario 3] / We chose [`total_score` opcional] / Accepting [no se puede auditar un puntaje fallido si el motor ni siquiera terminó el cálculo] |
| `userId` autenticado corresponde a `client.client_id` | Because [el contexto de autenticación vive en el token, no en el modelo de encuestas] / We chose [pasar `userId` (`user_id` en Python) como parámetro en las operaciones de repositorio; el filtro `WHERE client_id = :userId` es la última línea de defensa] / Accepting [el repositorio recibe el identificador autenticado y filtra por `client_id`; no valida el token, responsabilidad de la capa API] |
| `survey.status` sin `ERROR` | Because [el `01` §3.2 y `BR-03`/`BR-06` separan el ciclo de la encuesta del ciclo de la evaluación] / We chose [solo `DRAFT` y `COMPLETED` en `survey.status`; `ERROR` vive en `financial_profile.evaluation_status`] / Accepting [un fallo del motor no reabre la encuesta cerrada; el cliente ve la categoría provisional (fuera de alcance el reintento automático — §5)] |

```mermaid
erDiagram
    client ||--o{ survey : owns
    client ||--o| financial_profile : has
    survey ||--o{ answer : records
    question ||--o{ answer : is answered as
    survey ||--o| financial_profile : originates

    client {
        uuid client_id PK
        string email UK
        datetime created_at
    }
    survey {
        uuid survey_id PK
        uuid client_id FK
        string status
        datetime started_at
        datetime completed_at
        datetime updated_at
    }
    question {
        int question_id PK
        string text
        decimal weight
        int display_order
        boolean is_required
        boolean is_active
    }
    answer {
        uuid answer_id PK
        uuid survey_id FK
        int question_id FK
        int selected_option
        decimal option_value
    }
    financial_profile {
        uuid profile_id PK
        uuid client_id FK
        uuid survey_id FK
        string assigned_category
        string evaluation_status
        decimal total_score
        datetime assigned_at
    }
```

| Entity / document type | Meaning in the system | Identifier | Constraints (required, unique, allowed values) |
|---|---|---|---|
| `client` | Persona autenticada dueña de encuestas y del perfil de inicio | `client_id` | `email` obligatorio y único. No hay clase `Client` en los diagramas del `01`: se persiste como identidad referenciada por `userId` (`user_id` en Python). |
| `survey` | Una ejecución del cuestionario de onboarding | `survey_id` | `status` ∈ {`DRAFT`, `COMPLETED`}. **`ERROR` no es un estado de encuesta.** `completed_at` solo si `status = COMPLETED`. A lo sumo un `DRAFT` por `client_id` (`BR-02`). Una vez en `COMPLETED`, no vuelve a `DRAFT` ni acepta `saveAnswer` (`BR-03`). |
| `question` | Pregunta parametrizada del cuestionario breve | `question_id` | `text` y `weight` obligatorios. `weight` ≥ 0 con tipo `NUMERIC`. `display_order` único dentro del catálogo activo. `is_active` indica si integra el cuestionario vigente. A lo sumo 10 preguntas activas (`BR-01`). |
| `answer` | Opción elegida por el cliente en una pregunta de una encuesta | `answer_id` | Par (`survey_id`, `question_id`) único. `selected_option` entero positivo y válido para la pregunta según el catálogo de opciones acordado; `option_value` `NUMERIC` no nulo, resuelto por el backend a partir de esa opción. Se inserta o actualiza vía `saveAnswer` por transacción independiente. |
| `financial_profile` | Categoría de inicio vigente del cliente (`BR-04`) | `profile_id` | `client_id` único. `assigned_category` ∈ {`CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`, `UNDER_EVALUATION`}. `evaluation_status` ∈ {`COMPLETED`, `ERROR`}. Si `ERROR`, categoría = `UNDER_EVALUATION` y `total_score` nulo (`BR-06`). `survey_id` obligatorio (qué encuesta produjo el perfil). |

### 2.3 Data Ownership

Ningún componente lee ni escribe tablas de otro. PostgreSQL es el almacén, no el dueño de negocio. El dueño autoritativo es el componente que mantiene el invariante.

| Information | Authoritative owner (component responsible for maintaining it) | Consumed by (uses it without owning it) | Access through |
|---|---|---|---|
| Encuesta, estado y respuestas | Survey Module (`SurveyManager` + `SurveyRepository`) | Categorization Module (solo `List~ScoredAnswerDTO~` al evaluar) | `startSurvey`, `saveAnswer`, `resumeSurvey`, `completeSurvey`, `SurveyRepository` |
| Catálogo de preguntas y pesos | Survey Module (`SurveyRepository`) | `ScoringEngine` (consume `optionValue` y `weight` ya resueltos en `ScoredAnswerDTO`, no consulta SQL) | carga de encuesta en `startSurvey`/`resumeSurvey` y ensamblado de DTO en `completeSurvey` |
| Perfil financiero (categoría, estado de evaluación, puntaje) | Categorization Module (`CategorizationService` + `ProfileRepository`) | Web App (solo para mostrar confirmación y panel) | `evaluateProfile`, `ProfileRepository.saveCategory` / `findByUserId` |
| Identidad `client` / `userId` | **Fuera del alcance detallado** (módulo de autenticación no diseñado en Entrega 1) | Survey Module y Categorization Module (FK + parámetro inyectado; nunca actualizan email ni credenciales) | Dependencia de FastAPI `getCurrentUser()` (`get_current_user` en Python); parámetro `userId` en las operaciones de servicio y repositorio. **Nunca se lee de `request.body`.** |
| Matriz y umbrales `BR-05` | `ScoringEngine` (conocimiento interno, no fila persistida) | `CategorizationService` | `calculateScore`, `determineCategory` |
| Datos de tracking / banca externa | N/A — no existen en este sistema | Nadie | N/A |

### 2.4 Concurrencia y atomicidad de operaciones

Las restricciones de integridad de PostgreSQL se complementan con transacciones para evitar que peticiones concurrentes violen los invariantes:

| Operation | Concurrency strategy | Expected behavior |
|---|---|---|
| `startSurvey(userId)` | Insertar el `DRAFT` dentro de una transacción, respaldado por el índice único parcial `(client_id) WHERE status = 'DRAFT'`. Ante conflicto de unicidad, consultar y devolver el borrador que ganó la carrera. | Dos peticiones simultáneas no crean dos borradores; ambas obtienen el mismo `DRAFT`. |
| `saveAnswer(surveyId, userId, answer)` | `SurveyManager` valida ownership, estado `DRAFT` y validez en catálogo antes de persistir; `SurveyRepository` ejecuta la operación en transacción bloqueando la fila `survey` (`SELECT ... FOR UPDATE` o equivalente) con filtro `WHERE client_id = :userId` y hace el upsert de `answer`. | La comprobación de ownership/estado y la escritura quedan serializadas respecto a `completeSurvey`. |
| `completeSurvey(surveyId, userId)` | `SurveyManager` coordina la validación de ownership, estado `DRAFT` y respuestas obligatorias, mientras `SurveyRepository` bloquea la fila `survey` en transacción (`WHERE client_id = :userId`), actualiza a `COMPLETED` y fija `completed_at` antes de confirmar e invocar la evaluación. | Una respuesta concurrente se guarda antes de completar o es rechazada después; no hay escrituras tardías sobre una encuesta cerrada. |

La evaluación se ejecuta después de confirmar la transición a `COMPLETED`. Un fallo de evaluación no revierte la encuesta a `DRAFT`. La estrategia concreta de aislamiento y manejo de excepciones se implementa con PostgreSQL; no requiere un componente ni infraestructura adicional.

### 2.5 Business rules and invariants enforced in data

| Business rule or invariant | Where it is enforced (component logic / data constraint / both) | How |
|---|---|---|
| **`BR-01`** — acotación del cuestionario (máximo 10 preguntas, peso ≥ 0) | Both | Datos: a lo sumo 10 filas activas en `question` con `weight >= 0`. Lógica: `startSurvey` arma el cuestionario desde ese catálogo. |
| **`BR-02`** — unicidad de borrador (`DRAFT`) | Both | Datos: índice único parcial `(client_id) WHERE status = 'DRAFT'` en `survey`. Lógica: `startSurvey` y `resumeSurvey` devuelven el `DRAFT` existente sin duplicarlo. |
| **`BR-03`** — completitud e inmutabilidad al cierre (`COMPLETED`) | Both | Lógica: `SurveyManager.completeSurvey` exige respuestas en todas las `question` obligatorias y `SurveyManager.saveAnswer` rechaza si `status ≠ DRAFT`. Datos: `completed_at` inmutable una vez fijado. |
| **`BR-04`** — categoría única vigente por cliente | Both | Lógica: `CategorizationService.evaluateProfile` deja un único perfil vigente vinculado a `survey_id`. Datos: `client_id` único y `assigned_category` obligatorio en `financial_profile`. |
| **`BR-05`** — desempate conservador en el umbral (`<=`) | Component logic | Solo `ScoringEngine.determineCategory`. No hay columna "empate": el resultado ya es la categoría conservadora. |
| **`BR-06`** — asignación provisional ante fallo de evaluación | Both | Lógica: `CategorizationService.evaluateProfile` ante falla llama `saveCategory(..., UNDER_EVALUATION, ERROR)` con `totalScore = null` sin reabrir `survey`. Datos: coherencia entre categoría, estado `ERROR` y puntaje nulo en `financial_profile`. |
| Toda operación de lectura o escritura sobre `survey` y `financial_profile` filtra por `userId` | Both | Lógica: `SurveyManager` y `CategorizationService` reciben `userId` del contexto de autenticación. Datos: query con `WHERE client_id = :userId`. |
| `survey.status` no contiene `ERROR` | Data | El enum del `01` §3.2 define solo `{DRAFT, COMPLETED}`. El error vive en `financial_profile.evaluation_status`. |
| Una respuesta por pregunta y encuesta | Data | Unique (`survey_id`, `question_id`) en `answer`. `saveAnswer` hace upsert y valida la opción. |
| Escrituras concurrentes sobre una encuesta | Both | Transacciones y bloqueo de la fila `survey` para serializar `saveAnswer` y `completeSurvey`; índice único parcial para creación concurrente de `DRAFT`. |
| Los logs de aplicación no contienen respuestas, puntajes ni datos personales o financieros | Component logic | `logError(errorType, operation, timestamp)` — el contrato del método no acepta payloads de usuario. |
| Precisión decimal del puntaje | Data | `total_score`, `weight` y `option_value` como `NUMERIC` (`ADR-0001`), no punto flotante. |
| Si el `userId` no corresponde al dueño, la operación se rechaza con 404 (no 403) | Component logic | `findById` devuelve `null`; `SurveyRouter` traduce a 404 para no filtrar existencia. |

---

## 3. Interface Contract

**Interaction chosen** (from diagram 1.1, message `evaluateProfile` de `SurveyManager` hacia `CategorizationService`):
> Es el punto en el que el ciclo de vida de la encuesta entrega el control al cálculo de categoría. Ahí se concentran `BR-04`, `BR-05`, `BR-06`, la precisión decimal y el Escenario 3 (no bloquear al cliente con un 500). El detalle completo por operación de backend y frontera HTTP (`CT-01` a `CT-12`) se especifica en `docs/contracts/`.

### 3.1 Contrato detallado — `evaluateProfile`

| Element | Specification |
|---|---|
| **Operation and purpose** | `evaluateProfile(userId, surveyId, answers)`: calcular la categoría de inicio del cliente a partir de los `ScoredAnswerDTO` de una encuesta ya enviada y dejar el perfil persistido. Si el cálculo o la persistencia de la categoría definitiva fallan, intenta dejar una categoría provisional; solo puede garantizarlo si la escritura provisional tiene éxito. |
| **Input** (parameters and types) | `userId`: UUID no nulo del cliente autenticado. `surveyId`: UUID no nulo de la encuesta enviada. `answers`: lista no vacía de `ScoredAnswerDTO` (`questionId: int`, `optionValue: Decimal`, `weight: Decimal >= 0`). |
| **Output** (successful result and data structure) | `EvaluationResult { surveyId: UUID, assignedCategory: FinancialCategory, evaluationStatus: EvaluationStatus, totalScore: Decimal \| null }`. En éxito de cálculo: `evaluationStatus = COMPLETED`, `assignedCategory` ∈ {`CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`}, `totalScore` no nulo. |
| **Preconditions** (what the caller must satisfy before invoking) | El llamador (`SurveyManager`) ya validó ownership, estado `DRAFT` y respuestas obligatorias dentro de la transacción de finalización; la transición a `COMPLETED` (`BR-03`) se confirma antes de invocar este servicio. `userId` corresponde al dueño de `surveyId`. `answers` no está vacía. El catálogo usado para responder sigue siendo el vigente (no hay versionado — supuesto). |
| **Postconditions** (what is guaranteed on successful completion) | Existe exactamente un `financial_profile` para `userId` (`BR-04`). `assigned_category`, `evaluation_status` y `total_score` coinciden con el `EvaluationResult` devuelto. `survey_id` del perfil es el de esta invocación. `BR-05` ya está aplicada. |
| **Failure outcomes** (each failure, and what state is left after it) | `InvalidInputError` (`answers` vacía o `Decimal`/`weight` inválido): si ocurre antes de evaluar se rechaza sin alterar el perfil. Fallo de cálculo o de persistencia de la categoría definitiva: se registra un log sanitizado y se intenta `saveCategory(userId, ProfileEvaluation(surveyId, UNDER_EVALUATION, EvaluationStatus.ERROR, null))` (`BR-06`). Si la escritura provisional tiene éxito, se devuelve `EvaluationResult` con `evaluationStatus = ERROR`, categoría `UNDER_EVALUATION` y `totalScore = null`. Si también falla, se propaga `EvaluationPersistenceError`; no se garantiza que exista un perfil actualizado ni que `BR-04` pueda satisfacerse. La llamada a `logError(errorType, operation, timestamp)` **no incluye** respuestas, puntajes ni datos personales. La falla de la persistencia provisional se trata como `EvaluationPersistenceError` (`ADR-0005`) y queda registrada en §5; no se inventa una cola de reintentos (`ADR-0001`). En ningún caso se altera el contenido de `answer`. |
| **Invariants and side effects** (what must stay true, what may change) | No se reescriben respuestas. No se crea un segundo perfil para el mismo `userId` (upsert). `ScoringEngine` no persiste. La operación no es idempotente en el puntaje si el catálogo de pesos cambia entre llamadas, pero sí deja un único perfil vigente. Efecto de lado: escritura en `financial_profile`. |

**Testable examples**

| Case | Before | Request | Expected |
|---|---|---|---|
| Cálculo exitoso (Escenario 1) | Encuesta `COMPLETED` con 10 respuestas. Sin perfil, o perfil previo irrelevante. | `evaluateProfile(U1, S1, scoredAnswers[10])` con puntaje interior a una banda | `EvaluationResult(S1, categoría de esa banda, COMPLETED, totalScore)`. Una fila de perfil para `U1`. |
| Empate en umbral (`BR-05`) | Igual, puntaje exactamente en el límite entre Moderado y Conservador | `evaluateProfile(U1, S1, scoredAnswers)` | `assignedCategory = CONSERVATIVE` (menor riesgo), `evaluationStatus = COMPLETED`. |
| Falla del motor (Escenario 3) | Encuesta `COMPLETED`. `ScoringEngine` o `saveCategory` de éxito lanzan error | `evaluateProfile(U1, S1, scoredAnswers)` | `EvaluationResult(S1, UNDER_EVALUATION, ERROR, null)`. Perfil provisional persistido. En este caso, y solo en este caso, el cliente puede continuar al panel. Si también falla esa escritura, se produce `EvaluationPersistenceError`, no se garantiza el perfil y el acceso al panel debe resolverse según la decisión pendiente de §5. |
| Entrada inválida | Cualquiera | `evaluateProfile(U1, S1, [])` | `InvalidInputError`. Perfil intacto. |
| Reevaluación posterior | Perfil `COMPLETED` de encuesta `S0` | `evaluateProfile(U1, S2, scoredAnswers')` | Un solo perfil de `U1`, ahora con `survey_id = S2` y nueva categoría. `S0` permanece en historial de encuestas. |

Los umbrales numéricos exactos de cada banda **no** están en `REQ-01`. Los ejemplos anteriores son comprobables en forma, no en el valor del `Decimal` (§5).

### 3.2 Resumen de contratos del Survey Module

Las operaciones del Survey Module se documentan aquí con la misma disciplina que `evaluateProfile` y se detallan por operación en `docs/contracts/` (`CT-01` a `CT-12`):

| Operation | Input | Output | Preconditions | Postconditions | Failure outcomes |
|---|---|---|---|---|---|
| `startSurvey(userId)` | `userId`: UUID del contexto autenticado | `Survey` en `DRAFT` con `questions` cargadas | `userId` autenticado. | Existe exactamente un `DRAFT` para `userId` (idempotente: si ya existía, se devuelve el existente). Si no existía, se crea con `started_at = now()`. | `UnauthorizedError` (401) si el token no es válido. |
| `saveAnswer(surveyId, userId, answer)` | `surveyId`: UUID. `userId`: UUID del contexto autenticado. `answer`: `{ questionId, selectedOption }`; el backend valida la opción para esa pregunta y resuelve `optionValue: Decimal`. | `void` en `SurveyManager` (`SurveyRepository.saveAnswer` retorna `bool`). | Existe `survey` con `survey_id = surveyId` **y** `client_id = userId`, **y** `status = DRAFT`. `questionId` existe en el catálogo vigente. | La fila `answer` para (`surveyId`, `questionId`) queda insertada o actualizada. `survey.updated_at` se actualiza. | `NotFoundError` (404) si la encuesta no existe o no pertenece al `userId`. `InvalidStateError` (409) si `status = COMPLETED` (incluyendo cuando `SurveyRepository.saveAnswer` retorna `false` bajo bloqueo pesimista). `ValidationError` (422) si `questionId` o la opción no son válidos. **En todos los casos, sin alterar datos existentes.** |
| `resumeSurvey(userId)` | `userId`: UUID del contexto autenticado. | `Survey DRAFT \| null` con `answers` y `questions` cargadas. | `userId` autenticado. | Devuelve el `DRAFT` del usuario (con todas las `answer` persistidas) o `null` si no existe. No modifica estado. | `UnauthorizedError` (401) si el token no es válido. |
| `completeSurvey(surveyId, userId)` | `surveyId`: UUID. `userId`: UUID del contexto autenticado. | `EvaluationResult` (delegado de `evaluateProfile`, incluyendo `evaluationStatus`). | Existe `survey` con `survey_id = surveyId` **y** `client_id = userId`, **y** `status = DRAFT`, **y** todas las `question` obligatorias tienen `answer`. | `survey.status = COMPLETED` y `completed_at = now()`. Construye `List<ScoredAnswerDTO>` e invoca `evaluateProfile(userId, surveyId, scoredAnswers)`. Devuelve su `EvaluationResult`. | `NotFoundError` (404) si la encuesta no existe o no es del `userId`. `InvalidStateError` (409) si ya está `COMPLETED`. Si el cliente perdió la respuesta HTTP de una finalización exitosa, debe poder consultar el perfil vigente (`ProfileRepository.findByUserId` / endpoint de consulta en `CategorizationRouter`); esa ruta HTTP queda por formalizar en contrato. `ValidationError` (422) si faltan respuestas obligatorias. |
| `findById(surveyId, userId)` | `surveyId`: UUID. `userId`: UUID del contexto autenticado. | `Survey (DRAFT o COMPLETED) \| null`. | — | Devuelve la encuesta, sea `DRAFT` o `COMPLETED`, **solo** si `client_id = userId`. No modifica estado. | Ningún error explícito: devuelve `null` cuando no existe o no es del `userId`. El Router traduce `NotFoundError` a 404 (nunca 403, para no filtrar existencia; `ADR-0006`). |

**Nota de atomicidad:** `saveAnswer` y la transición de `completeSurvey` validan ownership/estado y escriben dentro de transacciones con bloqueo pesimista de la fila `survey` (`ADR-0004`). La evaluación se invoca después del commit de `COMPLETED` (`ADR-0005`).

**Nota sobre el nivel de detalle:** `evaluateProfile` merece el contrato completo por su centralidad (`BR-04`, `BR-05`, `BR-06`, precisión decimal, Escenario 3). El desglose completo de precondiciones, postcondiciones, invariantes y traducciones HTTP para todas las operaciones vive en `docs/contracts/` (`CT-01` a `CT-12`).

---

## 4. Cross-Consistency & Changes to Deliverable 1

| Check | Result |
|---|---|
| Every participant in a sequence diagram is an actor, a component, a class, an external system or an explicit authentication dependency from Deliverable 1 | Cumple. `Cliente` es el actor (2.1). `Web App`, `SurveyRouter`, `SurveyRepository`, `ProfileRepository` son componentes (2.2). `SurveyManager`, `CategorizationService`, `ScoringEngine` son clases (3.2). `Auth Dependency` es una **dependencia de FastAPI** (`getCurrentUser` / `Depends(get_current_user)`), no un componente del sistema. No hay sistemas externos: `REQ-01` lo prohíbe. |
| Every message corresponds to a capability, operation or contract | Cumple. `startSurvey`, `saveAnswer`, `resumeSurvey`, `completeSurvey`, `evaluateProfile`, `calculateScore`, `determineCategory`, `findById`, `findDraftByUserId`, `save`, `saveCategory`, `findByUserId`, así como los DTOs/enums `ScoredAnswerDTO`, `ProfileEvaluation` y `EvaluationStatus`, están alineados con `01` y `docs/contracts/` (`CT-01`..`CT-12`). `getCurrentUser` (`get_current_user` en Python) es la dependencia de autenticación. |
| Every entity or document type is reflected in the class diagrams, or the reason it is not is stated | `survey`, `question`, `answer` ↔ clases `Survey`, `Question`, `Answer`. `financial_profile` ↔ `EvaluationResult` + `ProfileEvaluation` + `EvaluationStatus` + `FinancialCategory` + `FinancialProfile` + `ProfileRepository`. `client` no tiene clase: la Entrega 1 no diseñó autenticación; solo viaja como `userId` inyectado (`ADR-0006`). |
| Every persisted information element has exactly one authoritative owner | Cumple (§2.3 y `ADR-0003`). `client`/`userId` se declara fuera de los módulos seleccionados; el cruce entre `survey` y `categorization` usa `ScoredAnswerDTO` sin duplicar propiedad ni importar modelos ajenos. |
| The contract agrees with the sequence diagram and with the data model (same behavior in all three views) | Cumple. Los tres escenarios de §1.1 (éxito, error, inválido) coinciden con `EvaluationStatus.COMPLETED`, `EvaluationStatus.ERROR` e `InvalidInputError`/`InvalidStateError`. §1.2 corresponde con `resumeSurvey` y `findDraftByUserId`. §1.3 corresponde con `null → 404` de `findById` (`ADR-0006`). |

**Changes made to Deliverable 1 because of this deliverable**

> Se actualizó `docs/design/01_Architectural_and_Detailed_Design.md` (v1.1) y se reconcilió con `docs/contracts/` (`CT-01` a `CT-12`) y `ADR-0003`..`ADR-0006`:
>
> 1. **`SurveyStatus` (`01` §3.2):** se eliminó `ERROR` (queda `{DRAFT, COMPLETED}`) y se formalizó `EvaluationStatus {COMPLETED, ERROR}` en `EvaluationResult`, `ProfileEvaluation` y `FinancialProfile` (`CT-09`, `CT-12`).
> 2. **Persistencia progresiva y locks (`saveAnswer`):** reemplaza la operación batch `saveDraft`, retornando `Boolean` en `SurveyRepository.saveAnswer` bajo `SELECT ... FOR UPDATE` (`CT-06`, `CT-08`, `ADR-0004`), mientras `SurveyRepository.findById`, `findDraftByUserId` y `save` retornan `Optional~Survey~` (`CT-04`, `CT-05`, `CT-07`).
> 3. **Desacoplamiento por DTOs (`ScoredAnswerDTO` y `ProfileEvaluation`):** `CategorizationService.evaluateProfile` recibe `List~ScoredAnswerDTO~` (`CT-10`), `ScoringEngine` encapsula `thresholds` sin duplicar pesos (`CT-11`), y `ProfileRepository.saveCategory` recibe `(userId, ProfileEvaluation)` respetando el límite de ≤ 4 parámetros de `docs/code_style.md` (`CT-12`).
> 4. **Firmas con `userId` y aislamiento (`ADR-0003`, `ADR-0006`):** `findById(surveyId, userId)`, `saveAnswer(surveyId, userId, answer)`, `completeSurvey(surveyId, userId)` y `saveCategory(userId, evaluation)` materializan el filtro `WHERE client_id = :userId` en repositorio.
> 5. **Infraestructura y tolerancia síncrona (`ADR-0001`, `ADR-0005`):** no se añade módulo de autenticación ni broker de reintentos; `Auth Dependency` (`Depends(get_current_user)`) inyecta `userId` y el fallo doble de evaluación propaga `EvaluationPersistenceError`.

---

## 5. Open Questions

> **Umbrales numéricos de categoría.** `REQ-01` y `BR-05` definen el desempate en el límite, pero no los valores de cada banda. No se inventan cortes. Hasta que producto/finanzas entregue la matriz, `determineCategory` no es implementable con números reales; el contrato sí es implementable en forma.
>
> **Catálogo de opciones de respuesta.** `selected_option` identifica una opción y `option_value` es el valor Decimal que el backend resuelve para el motor. `REQ-01` no define el catálogo ni su representación física. Antes de implementar, debe acordarse cómo validar que una opción pertenece a una pregunta y cómo se obtiene su valor; no basta con aceptar cualquier entero positivo.
>
> **Fallo doble de persistencia provisional.** Si falla la evaluación y también falla `saveCategory(..., UNDER_EVALUATION, ERROR)`, no existe garantía de que el perfil quede disponible. No se debe afirmar que el cliente puede entrar al panel ni que `BR-04` o `BR-06` quedan satisfechas en ese caso. La respuesta de API/UI y la recuperación requieren una decisión del stakeholder. No se introduce una cola (`ADR-0001`).
>
> **Reintento automático de evaluación (fuera de alcance).** `docs/req/REQ-01.md` fue alineado eliminando el reintento en segundo plano, por lo que ya no existe discrepancia requisito-diseño ni se programa un worker o broker (`ADR-0001`). Un eventual reintento posterior queda únicamente como posible mejora futura fuera del alcance actual.
>
> **Versionado del catálogo de preguntas.** `question.is_active` identifica las preguntas del cuestionario vigente y permite limitar el catálogo activo a 10 (`BR-01`). Al persistir pesos en `question` sin versionado/snapshot, un cambio de enunciado, peso u opciones puede reinterpretar encuestas históricas. No hay requisito de auditoría histórica.
>
> **Descarte de un `DRAFT`.** El Escenario 2 cubre guardar y reanudar, no abandonar de forma explícita. No se define `cancelDraft`. Si el usuario quiere descartar un borrador y empezar de cero, no hay operación para ello. Queda pendiente con el stakeholder.
>
> **Disparo de `startSurvey`.** No está especificado en `01` cuándo se invoca. Supuesto de diseño de este documento: al primer acceso del usuario a la pantalla de onboarding, o al login si `resumeSurvey` devuelve `null`. Requiere validación con UX.
>
> **Módulo de autenticación y de Plan.** La precondición "cuenta creada" y el paso 6 "resumen del plan" se satisfacen por `userId` inyectado por `Depends(get_current_user)` y por presentación derivada de la categoría. No se diseñan aquí.

---

## 6. Optional — AI-Assisted Design Reflection

> Una recomendación generada por IA fue **añadir un módulo de autenticación separado** para gestionar sesiones, tokens y el ciclo de vida del `userId`, además de **persistir la matriz de ponderación y los umbrales `BR-05` como tablas editables** y **guardar el último `EvaluationResult` embebido dentro de `survey`** para "simplificar lecturas".
>
> **El equipo la modificó, no la copió.**
>
> - **Módulo de autenticación:** rechazado como componente nuevo. El alcance del semestre y el `01` no lo diseñan. En su lugar, se documenta que el `userId` llega como dependencia de FastAPI (`Depends(get_current_user)`) y que el filtro por `userId` en repositorios es la última línea de defensa, aun cuando el módulo de auth no esté diseñado en detalle. Esto es coherente con `ADR-0001` (rechaza microservicios por sobrecarga operacional) y con el alcance del `01`.
> - **Matriz y umbrales persistidos:** rechazado. Duplicaría la fuente de verdad y contradiría el ocultamiento de información del `01` §4. Se persistieron `weight` y `option_value` (parámetros de pregunta/respuesta que el cuestionario ya necesita), pero los umbrales y el desempate siguen ocultos en `ScoringEngine`.
> - **`EvaluationResult` embebido en `survey`:** rechazado. `BR-04` coloca la categoría vigente en el cliente vinculada a su encuesta origen, manteniendo la entidad de perfil separada del historial de encuestas. Duplicar la categoría en `survey` y en un JSON de resultado crearía dos dueños para el mismo hecho, contradiciendo §2.3. Se acepta el costo de un `JOIN` perfil–encuesta y un upsert en `financial_profile`.
>
> Otra sugerencia de IA (cola de mensajes para el Escenario 3) se **rechazó de nuevo**, igual que en el `01` / `ADR-0001`: el contrato devuelve un `EvaluationResult` síncrono cuando la persistencia definitiva o provisional permite establecer un resultado (`BR-06`); si también falla la persistencia provisional, propaga `EvaluationPersistenceError`. El reintento en segundo plano no se implementa y quedó eliminado también de `docs/req/REQ-01.md`.

---

## 7. Consistency Checklist

- [x] Three interaction views derived from the single documented use case in REQ-01; they are not three independent use cases.
- [x] Each sequence diagram shows the main flow and at least one alternative or exception flow.
- [x] No business behavior is invented: anything unspecified is marked as an assumption or Open Question.
- [x] Section 2.1 explains what is NOT persisted as well as what is.
- [x] The data model has identifiers, relationships and constraints, not only boxes.
- [x] Every piece of principal information has one authoritative owner, and consumers are listed (Section 2.3).
- [x] The contract defines input, output, preconditions, postconditions and failure outcomes.
- [x] Sequence, data model and contract describe the same behavior.
- [x] Diagrams render correctly on GitHub (or the exported images are embedded).
