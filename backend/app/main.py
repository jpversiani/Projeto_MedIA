"""Aplicação FastAPI do Projeto MedIA (PEC) — sandbox dos componentes C29 e C30.

* C29 — indicador e armazenamento local de sincronização offline do PEC.
* C30 — Painel Lateral do Copiloto na tela do médico (Home Office), cujo
  artefato de front-end é ``backend/app/static/js/copiloto_sidebar.js``.
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.bootstrap import run_migrations, bootstrap_demo_data

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("media")

# O console do Windows usa cp1252 por padrão. Qualquer `print()` com acento ou
# símbolo levanta UnicodeEncodeError e, se ocorrer dentro do lifespan, derruba
# o servidor inteiro no boot — foi o que travava a v1 no Windows.
for _stream in (sys.stdout, sys.stderr):
    try:
        if _stream is not None and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover - depende do ambiente
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Falha rápida e explícita se a configuração expor dados de saúde
    # (chave JWT padrão, seed de demonstração, login demo, SSO sem JWKS).
    settings.validar_ambiente()

    # O schema passa a ser aplicado pelo Alembic (versionado e reprodutível),
    # e não mais por `Base.metadata.create_all()`, que nunca altera tabelas.
    if settings.AUTO_MIGRATE_ON_STARTUP:
        run_migrations()
    bootstrap_demo_data()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema Clínico MedIA - Consultório Particular, Convênios e Telemedicina",
    lifespan=lifespan,
)

# `allow_origins=["*"]` combinado com `allow_credentials=True` é inseguro: a
# origem passa a ser refletida junto dos cookies de sessão, o que equivale a
# permitir qualquer site a emitir requisições autenticadas. A lista de origens
# vem do ambiente (CORS_ORIGINS).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_V1_STR)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):  # pragma: no cover - depende do empacotamento
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_landing():
        landing_path = os.path.join(static_dir, "landing.html")
        if os.path.exists(landing_path):
            return FileResponse(landing_path)
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.get("/app", include_in_schema=False)
    @app.get("/cockpit", include_in_schema=False)
    async def serve_cockpit():
        return FileResponse(os.path.join(static_dir, "index.html"))


def custom_openapi():
    """Publica o esquema `securitySchemes`, que estava ausente.

    Sem ele, o Swagger não oferece o botão "Authorize" e clientes/gateways não
    descobrem que a API usa `Authorization: Bearer <token>`.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    components = schema.setdefault("components", {})
    components["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Token emitido por `POST /api/v1/auth/login`.",
        }
    }
    if settings.require_auth:
        schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

