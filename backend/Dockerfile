FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY scripts ./scripts

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m scripts.seed_phase0 && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
