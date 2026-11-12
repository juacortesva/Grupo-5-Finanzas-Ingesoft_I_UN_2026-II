#!/usr/bin/env bash
# Prueba de humo por CLI del Walking Skeleton (sin navegador).
# Uso: ./scripts/smoke_test.sh [URL_BASE]   (por defecto http://localhost:8000)
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
DEMO_USER_ID="11111111-1111-1111-1111-111111111111"

echo "1) GET  ${BASE_URL}/api/v1/health"
curl -fsS "${BASE_URL}/api/v1/health"
echo

echo "2) POST ${BASE_URL}/api/v1/surveys/start (X-User-Id demo)"
curl -fsS -X POST -H "X-User-Id: ${DEMO_USER_ID}" \
  "${BASE_URL}/api/v1/surveys/start"
echo

echo "OK: FastAPI -> SQLAlchemy -> PostgreSQL responde."
