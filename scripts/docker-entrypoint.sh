#!/bin/sh
# Entrypoint da imagem MedIA.
#
# 1. Aplica as migrações Alembic até `head` (idempotente).
# 2. Sobe o Uvicorn.
#
# As migrações rodam aqui, e não apenas no lifespan, para que o contêiner
# falhe cedo e de forma visível se o banco estiver inacessível — em vez de
# responder /health 200 com o schema pela metade.
set -eu

echo "[entrypoint] aplicando migrações Alembic..."
python - <<'PY'
from app.core.bootstrap import run_migrations

run_migrations()
PY

echo "[entrypoint] iniciando API..."
exec uvicorn app.main:app \
    --app-dir backend \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --proxy-headers \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}"
