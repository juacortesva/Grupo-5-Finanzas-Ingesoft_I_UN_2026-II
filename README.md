# Asesor Financiero Personal — Grupo 5 (Ingeniería de Software I, UNAL 2026-II)

Monorepo del proyecto: `backend/` (FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL),
`frontend/` (React + Vite + TypeScript) y `docs/` (requerimientos, ADR y diseño).

Estado actual: **Fase 0 — Walking Skeleton** (`docs/adr/adr_0002.md`). El objetivo
es demostrar que una petición viaja `React → FastAPI → SQLAlchemy → PostgreSQL`
y de regreso, con `pytest` en verde. Aún **no** hay lógica de negocio
(`ScoringEngine`, `evaluate_profile`, guardado o cierre de encuestas): eso llega
en los *Vertical Slices* 1–3. La tabla `financial_profile` ya existe porque la
migración inicial deja listo el modelo ER completo.

```text
.
├── docker-compose.yml        # PostgreSQL 16 solo para desarrollo local
├── backend/
│   ├── .env.example          # Variables de entorno (copiar a .env)
│   ├── pyproject.toml        # Dependencias, Ruff, Mypy, Pytest
│   ├── alembic/versions/     # 8cedce29f65b (tablas) → e4a1ef71cbd4 (constraints)
│   ├── scripts/
│   │   ├── seed_demo.py      # Cliente demo + 3 preguntas (idempotente)
│   │   └── smoke_test.sh     # Prueba de humo por CLI con curl
│   ├── src/                  # core/, survey/, categorization/, main.py
│   └── tests/                # unit/ e integration/ (transacción con rollback)
└── frontend/
    ├── .env.example          # VITE_API_URL
    └── src/                  # Página de verificación en texto plano
```

## Endpoints del Walking Skeleton

| Método | Ruta | Qué demuestra |
|---|---|---|
| `GET` | `/api/v1/health` | FastAPI vivo **y** `SELECT 1` en PostgreSQL (503 si la BD no responde) |
| `POST` | `/api/v1/surveys/start` | Router → `SurveyManager` → repositorio → PostgreSQL: crea o recupera el `DRAFT` y devuelve el catálogo |
| `GET` | `/docs` | Contrato OpenAPI (fuente de los tipos TypeScript) |

El `userId` nunca viaja en el body: se toma de la cabecera `X-User-Id`. Con
`DEMO_MODE=true`, si falta la cabecera se usa el cliente demo
`11111111-1111-1111-1111-111111111111`. Un `userId` que no exista en `client`
responde **401**.

## Requisitos

- Python 3.11+ y `git`
- Node.js 18+ y `npm` (solo para el frontend)
- PostgreSQL 16: con Docker en local, o la base de datos provista en la VM

## 1. Arranque local

```bash
git clone https://github.com/juacortesva/Grupo-5-Finanzas-Ingesoft_I_UN_2026-II.git
cd Grupo-5-Finanzas-Ingesoft_I_UN_2026-II

# Base de datos
docker compose up -d
docker compose ps                      # esperar STATUS = healthy

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                   # ya apunta al Postgres del compose
alembic upgrade head                   # crea tablas y constraints
python -m scripts.seed_demo            # cliente demo + 3 preguntas
pytest                                 # debe quedar todo en verde
uvicorn src.main:app --reload --port 8000

# En otra terminal: prueba por CLI
cd backend && ./scripts/smoke_test.sh

# Frontend (otra terminal)
cd frontend
npm install
cp .env.example .env
npm run dev                            # abrir http://localhost:5173
```

En la página, el botón **GET /api/v1/health** debe mostrar
`{"status": "ok", "database": "ok"}` y **POST /api/v1/surveys/start** debe mostrar
`status=DRAFT preguntas=3`.

## 2. Despliegue en la VM del curso (PuTTY / SSH)

La VM usa la base de datos entregada por el profesor, así que **no** se necesita
Docker allí. Las credenciales reales van **solo** en `backend/.env` dentro de la
VM; nunca en `.env.example` ni en commits.

```bash
# 1. Conectarse por PuTTY/SSH y clonar
git clone https://github.com/juacortesva/Grupo-5-Finanzas-Ingesoft_I_UN_2026-II.git
cd Grupo-5-Finanzas-Ingesoft_I_UN_2026-II/backend

# 2. Si falta el módulo venv (requiere sudo):
#    sudo apt update && sudo apt install -y python3-venv python3-pip
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 3. Configurar el .env privado de la VM
cp .env.example .env
nano .env
#   DATABASE_URL=postgresql+psycopg://<usuario>:<clave>@<host>:5432/<bd>
#   CORS_ORIGINS=http://localhost:5173,http://<IP_DE_LA_VM>:5173

# 4. Migrar, cargar datos demo y probar
alembic upgrade head        # el usuario de BD necesita permiso CREATE en el esquema
alembic current             # debe mostrar e4a1ef71cbd4 (head)
python -m scripts.seed_demo
pytest                      # usa transacciones con rollback: no deja datos

# 5. Levantar la API (nohup o tmux para que siga corriendo al cerrar PuTTY)
nohup uvicorn src.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
ss -tulpn | grep 8000       # verificar que escucha
./scripts/smoke_test.sh     # prueba de humo dentro de la VM

# 6. Frontend (si la VM tiene Node 18+)
cd ../frontend
npm install
cp .env.example .env && nano .env    # VITE_API_URL=http://<IP_DE_LA_VM>:8000
nohup npm run dev > vite.log 2>&1 &
```

Si los puertos 8000 o 5173 no están abiertos en el firewall de la VM, se puede
probar desde el PC con un túnel SSH (PuTTY → *Connection → SSH → Tunnels*, o):

```bash
ssh -L 8000:localhost:8000 -L 5173:localhost:5173 <usuario>@<IP_DE_LA_VM>
# luego abrir http://localhost:5173 en el navegador local
```

Para detener los procesos: `pkill -f uvicorn` y `pkill -f vite`.

## 3. Calidad y contrato

```bash
# backend/
ruff check . && ruff format --check . && mypy src scripts && pytest

# frontend/
npm run lint && npm run format:check && npm run typecheck
npm run gen:api       # con el backend corriendo: regenera src/api/generated/schema.d.ts
```

Las nuevas migraciones (`alembic revision --autogenerate -m "..."`) pasan por
`ruff check --fix` y `ruff format` automáticamente (`post_write_hooks` en
`alembic.ini`).

`DATABASE_URL` también puede reemplazarse solo para las pruebas con
`TEST_DATABASE_URL`. Cada prueba corre en una transacción que se revierte, así que
no depende de datos precargados ni modifica la base de datos.

## Documentación

- Requerimiento: `docs/req/REQ-01.md`
- Decisiones: `docs/adr/adr-0001.md`, `docs/adr/adr_0002.md`
- Diseño: `docs/design/01_Architectural_and_Detailed_Design.md`,
  `docs/design/02_Interaction_and_Data_Design.md`
- Convenciones: `docs/code_style.md`, `docs/estructura_repositorio.md`
- Estado del proyecto: `docs/project_status.md`
