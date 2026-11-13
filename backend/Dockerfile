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
# COPY conserva los permisos del host. En la VM la carpeta del equipo es
# rw-rw---- (solo el grupo team5), así que appuser no podría leer el código:
# se da lectura a todos dentro de la imagen (no cambia nada en la VM).
RUN useradd --create-home appuser \
    && chmod -R a+rX /app \
    && chmod a+x entrypoint.sh
USER appuser

EXPOSE 8000
CMD ["./entrypoint.sh"]
