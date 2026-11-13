# REQ-01 — Categorización Inicial de Situación y Hábitos Financieros

| | |
|---|---|
| **Status** | Validated (alineado con Diseño 2) |
| **Team / Author(s)** | Grupo 5 — Sistema de Planificación Financiera<br>• Esteban David Suárez<br>• Juan David Cortés<br>• Joel Felipe Suárez<br>• Kevin Facid Verjan |
| **Date** | 2026-10-08 (revisado 2026-11-12) |
| **Linked User Story / AC** | US-01, AC-01.1, AC-01.2, AC-01.3 |

---

## 1. Overview

**Requirement Statement**

> El sistema debe catalogar la situación y hábitos financieros del cliente mediante una encuesta breve para asignar una categoría de inicio en el plan.

**Type:** Functional *(con restricciones no funcionales verificables de tiempo, precisión numérica, seguridad y privacidad)*  
*(Filtro de Tecnología Perfecta: incluso disponiendo de velocidad infinita, memoria ilimitada, cero fallos y costo cero, el cliente aún necesita que el sistema evalúe sus respuestas e identifique su perfil/categoría inicial para personalizar su plan financiero. El comportamiento no desaparece.)*

**Source / Evidence**

> Ficha de Descubrimiento, Evidencia E-01 — Entrevistas con stakeholders y análisis de onboarding: "Los usuarios abandonan el proceso de registro si se les pide información contable o bancaria exhaustiva desde el primer día. Requieren una evaluación inicial rápida (menos de 3 minutos) que identifique su situación actual y les asigna un punto de partida claro."

**Need**

> Conocer mi perfil financiero de inicio de manera ágil sin tener que ingresar datos detallados o complejos.

**Value / Rationale**

> Permitir la personalización del plan financiero desde el primer momento, incrementando la tasa de conversión y retención durante el proceso de incorporación (onboarding) al reducir la fricción inicial.

---

## 2. Context — A Requirement Rarely Stands Alone

**Business Rule(s) (Dominio)**

> **BR-01 — Acotación del cuestionario:** La encuesta activa consta de un máximo de 10 preguntas parametrizadas, con peso no negativo asignado a cada pregunta.  
> **BR-02 — Unicidad de borrador (`DRAFT`):** Un cliente puede mantener a lo sumo una encuesta en estado `DRAFT` a la vez; si interrumpe la sesión y reingresa, retoma ese mismo borrador conservando las respuestas guardadas.  
> **BR-03 — Completitud e inmutabilidad al cierre (`COMPLETED`):** Una encuesta solo puede confirmarse y pasar a estado `COMPLETED` cuando todas las preguntas obligatorias tienen una respuesta válida. Una vez en `COMPLETED`, es inmutable: no puede volver a `DRAFT` ni aceptar nuevas respuestas o modificaciones.  
> **BR-04 — Categoría única vigente por cliente:** Todo cliente que completa la encuesta obtiene exactamente una categoría financiera inicial vigente (`CONSERVATIVE`, `MODERATE`, `AGGRESSIVE` o provisional `UNDER_EVALUATION`), vinculada a la encuesta que la originó.  
> **BR-05 — Desempate conservador en umbral:** Cuando la puntuación ponderada obtenida coincide exactamente con el límite (`<=`) entre dos categorías financieras, el sistema asigna por defecto la categoría de menor riesgo (más conservadora).  
> **BR-06 — Asignación provisional ante fallo de evaluación:** Si tras cerrar la encuesta en `COMPLETED` falla el cálculo o el guardado de la categoría definitiva, el sistema asigna la categoría provisional `UNDER_EVALUATION` (estado de evaluación `ERROR` y puntaje nulo) sin reabrir ni alterar la encuesta cerrada.

**Constraint(s) y Criterios No Funcionales Verificables**

> * **Alcance funcional (Restricción):** La categorización debe resolverse internamente en la aplicación a partir de las respuestas del cliente, sin integraciones con APIs bancarias ni lectura de extractos externos.
> * **Usabilidad / Tiempo (No funcional):** El cuestionario acotado por `BR-01` debe poder diligenciarse en un tiempo medio inferior a 3 minutos.
> * **Precisión numérica (No funcional):** El cálculo de puntajes y ponderaciones debe ejecutarse con aritmética decimal exacta (sin errores de redondeo por punto flotante).
> * **Seguridad y privacidad (No funcional):** Toda lectura o escritura debe restringirse al propietario autenticado sin revelar la existencia de recursos ajenos, y está prohibido registrar respuestas, puntajes o datos personales identificables (PII) en los logs de aplicación.

**Assumption(s)**

> Las respuestas autoreportadas por el cliente en la encuesta reflejan con suficiente fidelidad su realidad financiera para determinar una categoría de partida válida.

**Dependenc(ies)**

> Matriz o algoritmo de ponderación financiera, catálogo de opciones y umbrales numéricos definidos por el área de producto/finanzas para mapear las combinaciones de respuestas a las categorías (`CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`).

**Risk(s)**

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Acceso, divulgación o modificación no autorizados de los datos personales y respuestas financieras del usuario durante el diligenciamiento, procesamiento o almacenamiento de la encuesta, comprometiendo la confidencialidad, privacidad e integridad de la información. | Media | Alto | Obtener la identidad del usuario exclusivamente desde su sesión autenticada (nunca desde el cuerpo de la petición); validar propiedad en toda lectura y escritura de encuestas y perfiles rechazando recursos ajenos sin confirmar su existencia; garantizar la inmutabilidad de encuestas en estado `COMPLETED` (`BR-03`); proteger la comunicación en tránsito mediante HTTPS/TLS; prohibir estrictamente el registro de respuestas, puntajes o PII en los logs de aplicación; y aplicar principio de mínimo privilegio en los permisos de acceso a datos. |

**Open Questions**

> Ninguna a nivel de comportamiento funcional (el desempate en umbrales quedó definido en `BR-05`). Los valores numéricos exactos de los umbrales y el catálogo de opciones por pregunta permanecen sujetos a la definición de producto/finanzas (Dependencia).

---

## 3. Priority & Estimation

**Priority model used:** MoSCoW

**Priority assigned:**

> Asignamos **Must have**. La categorización inicial es el punto de entrada del flujo de onboarding financiero (`BR-04`). Consideramos **Should have**, pero se rechazó porque omitir la categorización inicial impide perfilar al cliente desde su ingreso.

**Estimate (confidence):** High

> La captura progresiva de respuestas mediante formularios y la aplicación de un modelo de puntuación parametrizado son patrones estándar y bien comprendidos por el equipo.

---

## 4. Representations — Requirement ≠ Representation

### 4.1 User Story

> Como **cliente nuevo**,  
> quiero **completar una encuesta breve sobre mi situación y hábitos financieros**,  
> para **obtener mi categoría financiera inicial**.

### 4.2 Acceptance Criteria

**Scenario 1 — Categorización exitosa tras encuesta completa**

> **Given** que el cliente se encuentra en la etapa de onboarding con una encuesta en estado `DRAFT` (`BR-02`)  
> **When** responde la totalidad de las preguntas obligatorias y confirma el envío (`BR-03`)  
> **Then** el sistema transiciona la encuesta a estado `COMPLETED` (inmutable), calcula su puntuación con precisión decimal exacta aplicando `BR-05` si corresponde, le asigna su categoría inicial vigente (`CONSERVATIVE`, `MODERATE` o `AGGRESSIVE`) con estado de evaluación `COMPLETED` (`BR-04`) y despliega la confirmación correspondiente.

**Scenario 2 — Abandono y reanudación de la encuesta (alternativo)**

> **Given** que el cliente ha respondido parcialmente la encuesta y cada respuesta ha sido guardada progresivamente en su único borrador `DRAFT` (`BR-02`)  
> **When** interrumpe la sesión o sale de la aplicación y vuelve a ingresar  
> **Then** el sistema conserva sus respuestas previas en estado `DRAFT` y le permite reanudar la encuesta ubicándolo en la primera pregunta obligatoria pendiente, sin perder el progreso guardado.

**Scenario 3 — Error de cálculo o persistencia de categoría (excepción)**

> **Given** que la encuesta ya fue confirmada en estado `COMPLETED` (`BR-03`) y ocurre una falla en el cálculo de la ponderación o en el guardado de la categoría definitiva  
> **When** el sistema procesa la evaluación de manera síncrona  
> **Then** registra únicamente el error técnico sin incluir respuestas, puntajes ni PII en los logs, asigna de forma provisional la categoría `UNDER_EVALUATION` con estado de evaluación `ERROR` y puntaje nulo (`BR-06`), informa la falla temporal al usuario y le permite continuar hacia la aplicación. Si también falla el guardado del perfil provisional, el sistema notifica al usuario que no pudo completarse la evaluación sin exponer detalles internos.

### 4.3 Use Case

| Field | |
| --- | --- |
| **Use Case name** | Catalogar Situación Financiera y Asignar Categoría |
| **Actor** | Cliente |
| **Goal** | Obtener una categoría financiera inicial mediante la resolución de una encuesta breve |
| **Trigger** | El cliente inicia o retoma el proceso de configuración inicial del perfil financiero |
| **Precondition** | El cliente ha creado una cuenta y se ha autenticado en la plataforma |

**Main Flow**

1. El cliente inicia la encuesta breve de hábitos y situación financiera (`BR-02` garantiza a lo sumo un `DRAFT` activo por cliente).
2. El sistema presenta las preguntas activas parametrizadas del cuestionario (`BR-01`).
3. El cliente responde progresivamente las preguntas obligatorias; cada respuesta válida se guarda individualmente mientras la encuesta permanece en `DRAFT`.
4. El cliente confirma el envío tras completar todas las preguntas obligatorias y el sistema cierra la encuesta en estado `COMPLETED` (`BR-03`).
5. El sistema evalúa de forma síncrona las respuestas contra la matriz de ponderación financiera (aplicando `BR-05` si el puntaje coincide con un umbral).
6. El sistema asigna y guarda la categoría inicial vigente en el perfil financiero del cliente (`BR-04`) con estado de evaluación `COMPLETED`.
7. El sistema presenta al cliente la confirmación con su categoría asignada.

**Alternative Flow**

> Encuesta incompleta / Abandono → Cada respuesta respondida ya fue guardada progresivamente en el borrador único en estado `DRAFT` (`BR-02`). Al reingresar, el sistema recupera el `DRAFT` del cliente con sus respuestas previas y lo posiciona en la primera pregunta obligatoria pendiente para completar la encuesta.

**Exception**

> Error en la evaluación o persistencia de categoría → Con la encuesta ya cerrada en estado `COMPLETED` (`BR-03`), si falla el cálculo o el guardado de la categoría definitiva, el sistema registra un log técnico sanitizado (sin respuestas, puntajes ni PII), persiste el perfil provisional con categoría `UNDER_EVALUATION`, estado de evaluación `ERROR` y puntaje nulo (`BR-06`), notifica la falla temporal al usuario y le permite continuar (sin reintento automático en segundo plano). Si también falla el guardado de la categoría provisional, el sistema informa al usuario que no fue posible completar la evaluación.

**Postcondition**

> La encuesta queda cerrada en estado `COMPLETED` (`BR-03`) y el cliente cuenta con una categoría inicial vigente en su perfil financiero (`BR-04`: `CONSERVATIVE`, `MODERATE`, `AGGRESSIVE` o provisional `UNDER_EVALUATION` por `BR-06`), salvo en el caso excepcional de fallo doble de persistencia.

**Flow Diagram**

```mermaid
flowchart TD
    A([Cliente inicia o retoma encuesta]) --> B["1-2. Sistema carga o crea único DRAFT (BR-02) y presenta preguntas (BR-01)"]
    B --> C["3. Cliente responde progresivamente; cada respuesta se guarda en DRAFT"]
    C --> D{"¿Completa obligatorias y confirma envío? (BR-03)"}
    D -- "Sí" --> G["4. Sistema cierra encuesta en COMPLETED (inmutable)"]
    G --> G2["5. Sistema evalúa respuestas contra matriz (BR-05)"]
    G2 -- "Éxito" --> G3["6-7. Sistema guarda categoría vigente (BR-04, COMPLETED) y confirma"]
    G3 --> H(["Postcondición: Categoría asignada al perfil"])

    D -- "No (abandona)" --> E["ALTERNATIVE: Progreso conservado en DRAFT; reanudar en 1.ª obligatoria pendiente"]
    E --> H2(["Postcondición: Borrador DRAFT pendiente"])

    G2 -- "Fallo cálculo o guardado" --> F["EXCEPTION: Log sin PII y guardado provisional UNDER_EVALUATION (BR-06, ERROR, puntaje nulo)"]
    F -- "Guardado provisional OK" --> H3(["Postcondición: Categoría provisional asignada"])
    F -- "Fallo doble de guardado" --> F2["EXCEPTION: Notificar fallo de evaluación sin alterar respuestas"]

    classDef mainflow fill:#1E2761,color:#ffffff,stroke:#1E2761;
    classDef alt fill:#F2A541,color:#1E2761,stroke:#F2A541;
    classDef exception fill:#B3261E,color:#ffffff,stroke:#B3261E;
    class B,C,G,G2,G3 mainflow;
    class E alt;
    class F,F2 exception;
```

---

## 5. Traceability & Impact

**Backward — why does this requirement exist?**

> Evidencia E-01 → Necesidad N-01 ("conocer mi perfil financiero de inicio de manera ágil") → REQ-01.

**Forward — what will this affect?**

> REQ-01 → Diseño Arquitectónico y Detallado (`docs/design/01_Architectural_and_Detailed_Design.md`) y Diseño de Interacción, Datos y Contratos (`docs/design/02_Interaction_and_Data_Design.md`) → Implementación → Pruebas (casos basados en AC-01.1, AC-01.2 y AC-01.3).

**Impact Analysis — if this requirement changes, what else might need to change?**

* [x] Business Rules
* [ ] Constraints
* [x] Dependencies
* [x] Risks
* [x] Acceptance Criteria
* [x] Estimate
* [ ] Priority
* [x] Future Design
* [x] Future Tests

> Si la estructura de la encuesta o la lógica de asignación de categorías cambia (ej. si se aumenta el número de preguntas o se requiere conexión bancaria directa), se verán afectadas las Reglas de Negocio (`BR-01` a `BR-06`), la matriz de ponderación (Dependencia), los Criterios de Aceptación, el diseño de interacción y datos y las pruebas automatizadas asociadas.

---

## 6. Validation — Quality Gate

* [x] **Valid?** Sí — proviene directamente de la evidencia E-01 y la necesidad de reducir la fricción en el onboarding.
* [x] **Clear / Unambiguous?** Sí — las reglas `BR-01` a `BR-06`, el flujo progresivo `DRAFT`, la inmutabilidad de `COMPLETED` y el manejo síncrono de fallos tienen una interpretación única.
* [x] **Atomic?** Sí — cubre exclusivamente la captura de la encuesta y la asignación de la categoría financiera inicial, sin acoplarse a módulos posteriores de recomendación o planes.
* [x] **Necessary?** Sí — sin la asignación de categoría inicial, el sistema no puede perfilar financieramente al cliente.
* [x] **Feasible?** Sí — realizable mediante formularios con guardado progresivo y reglas de puntuación sin infraestructura compleja externa.
* [x] **Verifiable?** Sí — comprobable mediante los criterios de aceptación AC-01.1 al AC-01.3.
* [x] **Consistent?** Sí — alineado con `docs/design/02_Interaction_and_Data_Design.md` y `docs/code_style.md`.
* [x] **Complete enough?** Sí — todas las reglas de dominio del ciclo de vida (`BR-01` a `BR-06`) y los escenarios de fallo están formalizados.
* [x] **Traceable?** Sí — cada sección conecta con evidencia previa, reglas de negocio, riesgos y artefactos de diseño específicos.
