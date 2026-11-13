# Imagen del backend (FastAPI). Se construye con: docker compose build backend
FROM python:3.12-slim

# Python sin archivos .pyc y con logs inmediatos en `docker compose logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Primero solo las dependencias: si el código cambia pero pyproject.toml no,
# Docker reutiliza esta capa y la reconstrucción es mucho más rápida.
COPY pyproject.toml ./
RUN mkdir -p src && touch src/__init__.py && pip install . && rm -rf src build

# Luego el resto del código.
COPY . .

# El proceso no corre como root dentro del contenedor.
RUN useradd --create-home appuser && chmod +x entrypoint.sh
USER appuser

EXPOSE 8000
CMD ["./entrypoint.sh"]
