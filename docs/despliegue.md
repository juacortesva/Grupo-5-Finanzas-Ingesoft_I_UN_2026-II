# Despliegue del team-5 en la VM del curso

| | |
|---|---|
| **VM** | `vm-learn-engsw1-2026ii-g1` |
| **Carpeta** | `/opt/projects-g1/team-5` |
| **Base de datos** | `g1-team-5-db` en el servidor PostgreSQL del curso (`34.69.97.140:5432`) |
| **Puerto publicado** | `3005` (pendiente de confirmar con el profesor) |

## 1. Cómo está armado

```
Navegador ──► VM:3005 ──► contenedor frontend (nginx)
                            ├── /        → archivos de React
                            └── /api/... → contenedor backend (FastAPI :8000)
                                              └──► g1-team-5-db (servidor del curso)
```

- **`backend/Dockerfile`**: receta de la imagen del backend. Instala Python y las dependencias de `pyproject.toml`. Al arrancar, `entrypoint.sh` aplica las migraciones de Alembic y luego levanta FastAPI.
- **`frontend/Dockerfile`**: compila React con Node y entrega el resultado a nginx.
- **`frontend/nginx.conf`**: sirve React y reenvía `/api/` al backend. Por eso el backend no publica ningún puerto y no hace falta CORS.
- **`docker-compose.yml`**: levanta los dos contenedores juntos con el nombre de proyecto `team-5`.
- **`.env`**: contraseña de la base de datos y puerto. **No se sube a GitHub.** Se crea a partir de `.env.example`.

## 2. Primer despliegue

Conectado a la VM por SSH:

```bash
cd /opt/projects-g1/team-5
git clone https://github.com/juacortesva/Grupo-5-Finanzas-Ingesoft_I_UN_2026-II.git .
```

El punto final (`.`) clona dentro de la carpeta actual, que debe estar vacía.

Crea el `.env` y completa la contraseña real de `g1_team_5_user`:

```bash
cp .env.example .env
nano .env
```

En `nano`: guarda con `Ctrl+O` y `Enter`; sal con `Ctrl+X`.

Construye y levanta:

```bash
docker compose up -d --build
```

La primera vez tarda unos minutos porque descarga las imágenes base y compila todo.

## 3. Verificar

```bash
docker compose ps
```

Deben aparecer `team-5-backend-1` y `team-5-frontend-1` con estado `Up`, y el frontend con `0.0.0.0:3005->80/tcp`.

```bash
curl http://localhost:3005/api/health
```

Respuesta esperada: `{"status":"ok","database":"ok"}`. Si dice `"database":"unreachable"`, revisa el `DATABASE_URL` del `.env`.

Para verlo en el navegador desde tu computador, si el puerto no está abierto en el firewall de Google Cloud, usa un túnel SSH desde tu PC:

```bash
ssh -L 3005:localhost:3005 <tu-usuario>@<ip-de-la-vm>
```

y abre `http://localhost:3005`. La documentación de la API queda en `http://localhost:3005/api/docs`.

## 4. Actualizar después de cambios en `main`

```bash
cd /opt/projects-g1/team-5
git pull
docker compose up -d --build
```

## 5. Comandos útiles

| Para | Comando |
|---|---|
| Ver logs del backend | `docker compose logs -f backend` (salir con `Ctrl+C`) |
| Ver logs del frontend | `docker compose logs -f frontend` |
| Reiniciar | `docker compose restart` |
| Detener | `docker compose down` |

**Reglas por ser una VM compartida:** ejecuta los comandos siempre dentro de `/opt/projects-g1/team-5` y solo con `docker compose`. No uses comandos globales como `docker system prune`, `docker stop $(docker ps -q)` o `docker rm` sobre contenedores que no empiecen por `team-5-`.

## 6. Desarrollo local (en tu computador)

Opción A, sin Docker:

```bash
# Terminal 1: backend
cd backend
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn src.main:app --reload

# Terminal 2: frontend
cd frontend
npm install
npm run dev                      # abre http://localhost:5173
```

El `.env` debe estar en `backend/` o exportado en la terminal. En desarrollo, Vite reenvía `/api` al backend local (ver `vite.config.ts`).

Opción B, con Docker, igual que en la VM: `docker compose up --build` desde la raíz y abrir `http://localhost:3005`.

Para no tocar la base de datos compartida mientras desarrollas o corres pruebas, levanta la base local:

```bash
docker compose --profile local-db up -d db
```

y usa en el `.env` la línea `DATABASE_URL` comentada de desarrollo local (puerto `5433`).
