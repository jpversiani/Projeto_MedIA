"""Aplicação FastAPI do Projeto MedIA (PEC) — sandbox dos componentes C29 e C30.

* C29 — indicador e armazenamento local de sincronização offline do PEC.
* C30 — Painel Lateral do Copiloto na tela do médico (Home Office), cujo
  artefato de front-end é ``backend/app/static/js/copiloto_sidebar.js``.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.api.v1.sincronizacao import router as sincronizacao_router
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema Clínico MedIA - Consultório Particular, Convênios e Telemedicina",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(sincronizacao_router, prefix=settings.API_V1_STR)

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

