# Estructura del Repositorio y Reglas de Módulos — Asesor Financiero Personal

| | |
| :--- | :--- |
| **Equipo** | Grupo 5 (`@KevinVerjan`, `@Estebandido-exe`, `@josuarezvi`, `@juacortesva`) |
| **Ubicación** | `docs/estructura_repositorio.md` |
| **Patrón de Organización** | Monorepo Políglota con **Backend y Frontend Modulares por Dominio y Capas Internas** |
| **Referencias** | `docs/adr/adr-0001.md`..`adr-0007.md`, `docs/design/`, `docs/contracts/` |

---

## 1. Principio de Organización

El repositorio se organiza como un **Monorepo** que agrupa la documentación de ingeniería (`docs/`), el servidor de aplicación (`backend/`) y la aplicación web cliente (`frontend/`). La base de datos PostgreSQL es externa (**`g1-team-5-db`**, provista por la cátedra) y se conecta mediante `DATABASE_URL` en `.env`, por lo que `docker-compose.yml` y los `Dockerfile` empaquetan únicamente **backend (FastAPI)** y **frontend (React/Vite)** para desarrollo reproducible y despliegue en la **VM del curso (`CentOS Stream 10`, directorio `/opt/projects-g1/team-5`)**.

Tanto en `backend/` como en `frontend/`, el código **no se agrupa en carpetas técnicas globales** (como un único directorio `models/` o `services/` para todo el sistema), sino que se divide primero por **Módulos de Dominio / Features** (por ejemplo, `survey/`, `categorization/`, `...`) y, dentro de cada módulo, se aplican las **capas arquitectónicas** definidas en `ADR-0001` (`docs/adr/adr-0001.md`: `router` $\rightarrow$ `service` $\rightarrow$ `repository` $\rightarrow$ `models`) y formalizadas en `ADR-0003`.

### Justificación
1. **Alineación con el Diseño Arquitectónico:** Refleja exactamente la división modular del sistema planteada en los diagramas de componentes.
2. **Cumplimiento del Data Ownership:** Cada módulo encapsula sus propias tablas y repositorios, evitando que un módulo acceda directamente a la persistencia de otro.
3. **Escalabilidad sin mantenimiento documental:** Al agregar un nuevo requerimiento o módulo de negocio, simplemente se añade una nueva carpeta de dominio siguiendo la misma plantilla interna sin alterar la estructura base.

---

## 2. Árbol de Directorios del Repositorio

El siguiente árbol define la jerarquía de carpetas y el patrón real de cada módulo en el repositorio:

```text
asesor-financiero/
├── README.md                        # Descripción general, ejecución local y despliegue en la VM
├── .env.example                     # Plantilla de variables de entorno (DATABASE_URL hacia g1-team-5-db)
├── .gitignore                       # Exclusiones de Git (.env, dependencias y artefactos de compilación)
├── docker-compose.yml               # Orquestación exclusiva de backend y frontend (VM CentOS Stream 10: /opt/projects-g1/team-5)
│
├── docs/                            # Documentación de Ingeniería de Software
│   ├── code_style.md                # Estándares de código y convenciones
│   ├── estructura_repositorio.md    # Este documento (arquitectura de carpetas)
│   ├── project_status.md            # Estado del proyecto y bitácora
│   ├── adr/                         # Architecture Decision Records (adr-0001.md a adr-0007.md)
│   ├── req/                         # Especificación de Requerimientos (REQ-01.md)
│   ├── design/                      # Entregables de Diseño Arquitectónico y de Datos
│   ├── contracts/                   # Contratos de interfaz por operación (CT-01 a CT-12)
│   └── rfc/                         # Requests for Comments (propuestas técnicas)
│
├── backend/                         # API REST y Lógica de Negocio (Python + FastAPI)
│   ├── Dockerfile                   # Imagen del servicio backend (FastAPI)
│   ├── entrypoint.sh                # Arranque del contenedor: alembic upgrade head + uvicorn
│   ├── pyproject.toml               # Dependencias y configuración de linters/pruebas
│   ├── alembic.ini                  # Configuración de Alembic
│   ├── alembic/                     # Migraciones de esquema sobre g1-team-5-db
│   │   ├── env.py                   # Importa src.core.models, src.survey.models y src.categorization.models
│   │   └── versions/                # (...) Archivos de migración versionados (0001_initial_schema.py)
│   ├── scripts/
│   │   └── seed_phase0.py           # Semilla idempotente con datos provisionales de calibración (Fase 0)
│   ├── src/
│   │   ├── main.py                  # Punto de entrada de FastAPI y registro de módulos
│   │   ├── core/                    # Infraestructura transversal (config.py, database.py, models.py, auth_deps.py, exceptions.py, schemas.py)
│   │   │   └── ...
│   │   │
│   │   ├── <domain_module>/         # Plantilla estándar por cada Módulo de Negocio
│   │   │   ├── router.py            # Capa HTTP (endpoints del módulo)
│   │   │   ├── service.py           # Capa de Aplicación / Orquestación + proveedor Depends del módulo
│   │   │   ├── engine.py            # (Opcional) Reglas matemáticas o de dominio puro
│   │   │   ├── repository.py        # Capa de Acceso a Datos (Interfaz + ORM)
│   │   │   ├── models.py            # Entidades SQLAlchemy exclusivas del módulo
│   │   │   ├── schemas.py           # DTOs Pydantic de entrada/salida
│   │   │   └── enums.py             # Enumeraciones y constantes del módulo
│   │   │
│   │   ├── survey/                  # Módulo de Encuestas (sigue plantilla <domain_module>)
│   │   │   └── ...
│   │   ├── categorization/          # Módulo de Categorización (sigue plantilla <domain_module>)
│   │   │   └── ...
│   │   └── ...                      # Futuros módulos de dominio
│   │
│   └── tests/                       # Suite de pruebas automatizadas por módulo de dominio (Pytest)
│       ├── conftest.py              # Fixtures de sesión (PostgreSQL real vía TEST_DATABASE_URL o fallback SQLite)
│       ├── survey/                  # Pruebas de contratos HTTP, repositorios e invariantes de survey
│       │   └── ...
│       └── categorization/          # Pruebas unitarias de ScoringEngine y resiliencia de CategorizationService
│           └── ...
│
└── frontend/                        # Aplicación Web Cliente (React + Vite + TypeScript)
    ├── Dockerfile                   # Imagen del servicio frontend (compilación con Node + nginx)
    ├── nginx.conf                   # Sirve el build de React y reenvía /api/ al backend
    ├── package.json                 # Dependencias y scripts de cliente
    ├── tsconfig.json                # Configuración estricta de TypeScript
    └── src/
        ├── api/                     # Cliente HTTP base (httpClient.ts), healthService.ts y tipos OpenAPI
        │   ├── generated/           # (...) Contratos TypeScript exportados desde FastAPI
        │   └── ...
        │
        ├── features/                # Módulos funcionales de UI (espejo de los módulos backend)
        │   ├── <feature_module>/    # Plantilla estándar por cada Feature de UI
        │   │   ├── api/             # (...) Puerto e implementaciones de adaptador API (HTTP real y mock)
        │   │   ├── components/      # (...) Componentes visuales propios del feature
        │   │   ├── hooks/           # (...) Custom hooks de estado y llamadas a la API
        │   │   ├── pages/           # (...) Vistas/pantallas completas del flujo
        │   │   └── types.ts         # Tipos e interfaces locales de la vista
        │   │
        │   ├── survey/              # Feature de Encuesta (sigue plantilla <feature_module>)
        │   │   └── ...
        │   ├── categorization/      # Feature de Categorización (sigue plantilla <feature_module>)
        │   │   └── ...
        │   └── ...                  # Futuros features de UI
        │
        └── shared/                  # Recursos transversales reutilizables sin dominio propio
            ├── components/          # (...) Banners, alertas y controles genéricos
            └── utils/               # (...) Formateadores y funciones auxiliares puras
```

---

## 3. Responsabilidades por Capa dentro de cada Módulo (`backend/src/<domain_module>/`)

Cada rol de archivo dentro de un módulo de dominio tiene responsabilidades estrictas para garantizar alta cohesión:

| Rol en el Módulo | Qué DEBE contener | Qué tiene PROHIBIDO contener |
| :--- | :--- | :--- |
| **`router.py`** | Definición de rutas HTTP, inyección del usuario autenticado (`user_id`) y traducción de excepciones de dominio a respuestas HTTP. | Consultas SQL/ORM, cálculos matemáticos, lógica de transición de estados o reglas de negocio. |
| **`service.py`** | Coordinación de casos de uso, validación de precondiciones, invocación a repositorios/motores y manejo de tolerancia a fallos. | Objetos HTTP (`Request`, `Response`, `HTTPException`), consultas directas de SQLAlchemy o detalles de infraestructura. |
| **`engine.py`** | Algoritmos y reglas de negocio o matemáticas puras operando exclusivamente con objetos en memoria y precisión `Decimal`. | Llamadas a repositorios, lecturas de base de datos, variables de entorno o librerías web. |
| **`repository.py`** | Contratos abstractos de persistencia y su implementación concreta con SQLAlchemy, aplicando siempre el filtro de propiedad por `user_id` (`WHERE client_id = :user_id` en BD). | Cálculos de negocio o decisiones de flujo de aplicación. |
| **`models.py`** | Definición declarativa de las tablas físicas de PostgreSQL de las cuales el módulo es dueño. | Lógica de aplicación o llamadas a servicios externos. |
| **`schemas.py`** | Contratos de datos (Pydantic DTOs) para validación de peticiones, respuestas y comunicación entre módulos. | Dependencias directas del ORM o sesiones de base de datos. |

---

## 4. Reglas de Dependencia e Importación

Para preservar el **bajo acoplamiento** y el **ocultamiento de información**, todas las importaciones deben cumplir dos leyes:

### 4.1 Ley de Dirección de Capas (Vertical dentro de un mismo módulo)
Las dependencias fluyen únicamente desde la frontera externa (HTTP) hacia el núcleo del dominio y la persistencia:

$$\text{router} \longrightarrow \text{service} \longrightarrow \begin{cases} \text{engine} \\ \text{repository} \longrightarrow \text{models} \end{cases}$$

* ❌ `service` **nunca** importa de `router`.
* ❌ `engine` **nunca** importa de `repository`, `models` ni `service`.
* ❌ `router` **nunca** importa directamente `repository` ni `models` (no puede saltarse la capa `service`).

### 4.2 Ley de Frontera entre Módulos y Data Ownership (Horizontal)
Ningún módulo de negocio puede leer ni escribir directamente en las tablas o repositorios de otro módulo:

* ✅ **Permitido:** El `service` de un módulo puede comunicarse con el `service` de otro módulo intercambiando únicamente DTOs (`schemas`) u objetos de dominio.
* ❌ **Prohibido:** Un módulo **jamás** puede importar `models.py` ni `repository.py` pertenecientes a otro `<domain_module>`.
* ✅ **Permitido:** Cualquier módulo puede importar utilidades transversales desde `src/core/`.
* ❌ **Prohibido:** `src/core/` **jamás** puede importar nada de ningún `<domain_module>` (evita dependencias circulares).

```python
# ❌ MAL: Un módulo importando directamente modelos o repositorios de otro módulo
from src.<other_module>.models import SomeDatabaseModel      # PROHIBIDO (Viola Data Ownership)
from src.<other_module>.repository import SomeRepository     # PROHIBIDO (Acoplamiento de datos)

# ✅ BIEN: Comunicación entre módulos exclusivamente a través de su capa de servicio y DTOs
from src.<other_module>.schemas import SomeResultDTO
from src.<other_module>.service import SomeDomainService
```

---

## 5. Convención Inmutable de Subcarpetas en `docs/`

Para mantener la trazabilidad sin enlaces rotos entre documentos, la carpeta `docs/` mantiene únicamente cinco subdirectorios de artefactos:

1. **`docs/req/`**: Especificaciones de requerimientos y casos de uso (no usar `docs/requirements/`).
2. **`docs/adr/`**: Registros de decisiones de arquitectura (no usar `docs/decisions/`).
3. **`docs/design/`**: Documentos de diseño arquitectónico, detallado, de interacción y de datos.
4. **`docs/contracts/`**: Contratos de interfaz detallados por operación (`CT-01` a `CT-12`).
5. **`docs/rfc/`**: Propuestas y borradores técnicos previos a una decisión formal.
