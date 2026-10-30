FROM python:3.12-slim

# Espelha o layout do repositório (/app/backend) para que `alembic.ini`,
# `backend/alembic` e `app` fiquem exatamente onde o código procura.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app

# Dependências de sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Criar usuário não-root para execução segura do contêiner
RUN adduser --disabled-password --gecos "" appuser

# Código da aplicação + migrações (o Alembic precisa dos dois para subir o
# schema em Postgres; antes só `backend/app` era copiado e o boot falhava).
COPY backend/app ./backend/app
COPY backend/alembic ./backend/alembic
COPY alembic.ini ./alembic.ini
COPY scripts/docker-entrypoint.sh ./scripts/docker-entrypoint.sh

RUN chmod +x ./scripts/docker-entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT:-8000}/health" || exit 1

# O entrypoint aplica as migrações (`alembic upgrade head`) antes de subir o
# servidor; sem isso, em Postgres, o seed e as rotas falhavam por falta de
# tabelas.
ENTRYPOINT ["./scripts/docker-entrypoint.sh"]
