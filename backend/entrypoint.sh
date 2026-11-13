#!/bin/sh
# Se ejecuta cada vez que arranca el contenedor del backend.
set -e

# 1. Aplica las migraciones pendientes (cuando el equipo agregue Alembic).
if [ -f alembic.ini ]; then
    echo "Aplicando migraciones de Alembic..."
    alembic upgrade head
else
    echo "alembic.ini no existe todavía: se omiten las migraciones."
fi

# 2. Arranca la API.
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
